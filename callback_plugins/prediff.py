# Callback plugin with prediff_cmd support
# Extends Ansible default callback plugin
#
# Usage (playbook):
# - hosts: localhost
#   gather_facts: no
#   tasks:
#     - copy:
#         src: cert.pem
#         dest: /tmp/cert.pem
#       vars:
#         prediff_cmd: openssl x509 -in %s -noout -text | head -n 10
#
# Here %s is replaced by temporary file path with content of `before`/`after`.
#
# Usage (execution):
# ANSIBLE_STDOUT_CALLBACK=prediff ansible-playbook -vv --check --diff test.yml
#
# Written by Konstantin Suvorov <dev@berlic.net>
# Visit ansibledaily.com for more Ansible tricks

from ansible.plugins.callback.default import CallbackModule as DefaultCallback
from subprocess import check_output, CalledProcessError, STDOUT
from tempfile import mkstemp
import os

try:
    from __main__ import display
except ImportError:
    display = None

class CallbackModule(DefaultCallback):

    def v2_on_file_diff(self, result):
        def process_diff(diff, cmd):
            for d in diff:
                for ab in ('after','before'):
                    fd, fn = mkstemp()
                    print fn
                    with open(fn, 'w') as f:
                        f.write(d[ab])
                    try:
                        new_cmd = cmd.replace('%s',fn)
                        res = check_output(new_cmd, stderr=STDOUT, shell=True)
                    except CalledProcessError as e:
                        display.warning('Error occured while calling prediff_cmd "{}": (Code {}) {}'.format(cmd, e.returncode, e.output))
                        res = None
                    os.unlink(fn)
                    if res:
                        d[ab] = res
            return diff

        if 'prediff_cmd' in result._task_fields['vars']:
            prediff_cmd = result._task_fields['vars']['prediff_cmd']
            if result._task.loop and 'results' in result._result:
                for res in result._result['results']:
                    if 'diff' in res and res['diff'] and res.get('changed', False):
                        res['diff'] = process_diff(res['diff'], prediff_cmd)
            elif 'diff' in result._result and result._result['diff'] and result._result.get('changed', False):
                result._result['diff'] = process_diff(result._result['diff'], prediff_cmd)
        return super(CallbackModule, self).v2_on_file_diff(result)
