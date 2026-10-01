"""Exercise queue races/recovery and DDC failures with two simulated monitors."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
MOCK = '''#!/usr/bin/env python3
import fcntl,json,os,sys,time
from pathlib import Path
root=Path(os.environ['MOCK_STATE'])
args=sys.argv[1:]
if args == ['detect','--brief']:
    print('Display 1\\n   I2C bus: /dev/i2c-10\\nDisplay 2\\n   I2C bus: /dev/i2c-12')
    sys.exit(0)
bus=args[args.index('--bus')+1]
if 'getvcp' in args:
    time.sleep(.03)
    current=json.loads((root/'values').read_text())[bus]
    print('VCP 10 C',current,100 if bus=='10' else 200)
else:
    with (root/'lock').open('w') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        values=json.loads((root/'values').read_text())
        target=int(args[args.index('setvcp')+2])
        values[bus]=target
        (root/'values').write_text(json.dumps(values))
        with (root/'writes').open('a') as log: log.write(bus+' '+str(target)+'\\n')
        # Simulate a write that applied but returned failure, on just one bus.
        if bus=='12' and (root/'fail').exists():
            (root/'fail').unlink()
            sys.exit(1)
'''


class BrightnessTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / 'ddcutil').write_text(MOCK)
        (self.root / 'ddcutil').chmod(0o755)
        (self.root / 'values').write_text(json.dumps({'10': 40, '12': 80}))
        self.env = dict(os.environ, MOCK_STATE=str(self.root),
                        XDG_RUNTIME_DIR=str(self.root),
                        PATH=f'{self.root}:/usr/bin:/bin')

    def tearDown(self):
        self.tmp.cleanup()

    def run_step(self, *args):
        return subprocess.Popen(['bash', str(ROOT / 'hypr/brightness-display-ddc.sh'), *args], env=self.env,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def finish(self, proc):
        out, err = proc.communicate(timeout=15)
        self.assertEqual(proc.returncode, 0, err.decode())

    def values(self):
        return json.loads((self.root / 'values').read_text())

    def test_rapid_turns_and_idle_handoff(self):
        for _ in range(4):
            procs = [self.run_step('up', '1') for _ in range(8)]
            for proc in procs:
                self.finish(proc)
        self.assertEqual(self.values(), {'10': 72, '12': 144})
        self.finish(self.run_step('down', '5'))
        self.assertEqual(self.values(), {'10': 67, '12': 134})

    def test_partial_write_retry_does_not_double_apply(self):
        (self.root / 'fail').touch()
        self.finish(self.run_step('up', '5'))
        self.assertEqual(self.values(), {'10': 45, '12': 90})
        writes = (self.root / 'writes').read_text().splitlines()
        self.assertEqual(writes.count('10 45'), 1)
        self.assertEqual(writes.count('12 90'), 2)

    def test_killed_worker_does_not_leave_stale_sentinel(self):
        state = self.root / 'klor-brightness-ddc'
        state.mkdir()
        (state / 'worker').touch()  # obsolete implementation's marker
        (state / 'pending').write_text('2\n')
        locker = subprocess.Popen(['python3', '-c', 'import fcntl,sys,time; f=open(sys.argv[1],"w"); fcntl.flock(f,fcntl.LOCK_EX); print("ready",flush=True); time.sleep(60)', str(state / 'worker.lock')], stdout=subprocess.PIPE)
        self.assertEqual(locker.stdout.readline().strip(), b"ready")
        self.finish(self.run_step('up', '3'))
        locker.kill()
        locker.wait()
        locker.stdout.close()
        self.finish(self.run_step("up", "1"))
        self.assertEqual(self.values(), {"10": 46, "12": 92})

    def test_clamps_to_each_monitor_range(self):
        self.finish(self.run_step('down', '100'))
        self.assertEqual(self.values(), {'10': 0, '12': 0})
        self.finish(self.run_step('up', '100'))
        self.assertEqual(self.values(), {'10': 100, '12': 200})

    def test_legacy_install_keeps_other_bindings(self):
        hypr = self.root / '.config/hypr'
        hypr.mkdir(parents=True)
        (hypr / 'bindings.conf').write_text('bind = SUPER, T, exec, true\n')
        subprocess.run(['python3', str(ROOT / 'hypr/install-brightness.py')],
                       env=dict(self.env, HOME=str(self.root)), check=True, capture_output=True)
        content = (hypr / 'bindings.conf').read_text()
        self.assertIn('bind = SUPER, T', content)
        self.assertEqual(content.count('bindeld ='), 4)

    def test_install_selects_lua_and_is_idempotent(self):
        hypr = self.root / '.config/hypr'
        hypr.mkdir(parents=True)
        (hypr / 'hyprland.lua').touch()
        (hypr / 'bindings.lua').write_text('o.bind("SUPER + T", "Mine", "true")\n')
        env = dict(self.env, HOME=str(self.root))
        for _ in range(2):
            subprocess.run(['python3', str(ROOT / 'hypr/install-brightness.py')], env=env, check=True, capture_output=True)
        content = (hypr / 'bindings.lua').read_text()
        self.assertIn('SUPER + T', content)
        self.assertEqual(content.count('dofile('), 1)
        self.assertTrue((hypr / 'brightness-display-ddc.sh').stat().st_mode & 0o100)


if __name__ == '__main__':
    unittest.main()
