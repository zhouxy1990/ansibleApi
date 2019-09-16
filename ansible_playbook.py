# -*- coding:utf-8 -*-
# CREATE BY Zhou Xiangyu
#!/usr/bin/env python


from collections import namedtuple
from ansible.parsing.dataloader import DataLoader
from ansible.vars.manager import VariableManager
from ansible.inventory.manager import InventoryManager
from ansible.executor.playbook_executor import PlaybookExecutor
from ansible.plugins.callback import CallbackBase
from operation_app import settings
import traceback
import logging
from result_transfer import get_result

class PlaybookCallbackBase(CallbackBase):
    """
    playbook的callback改写，格式化输出playbook执行结果
    """
    CALLBACK_VERSION = 2.0


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.task_ok = {}
        self.task_unreachable = {}
        self.task_failed = {}
        self.task_skipped = {}
        self.task_stats = {}


    def v2_runner_on_unreachable(self, result):
        """
        重写 unreachable 状态
        :param result:  这是父类里面一个对象，这个对象可以获取执行任务信息
        """
        self.task_unreachable[result._host.get_name()] = result

    def v2_runner_on_ok(self, result, *args, **kwargs):
        """
        重写 ok 状态
        :param result:
        """

        self.task_ok[result._host.get_name()] = result

    def v2_runner_on_failed(self, result, *args, **kwargs):
        """
        重写 failed 状态
        :param result:
        """
        self.task_failed[result._host.get_name()] = result


    def v2_runner_on_skipped(self, result):
        self.task_skipped[result._host.get_name()] = result

    def v2_playbook_on_stats(self, stats):
        hosts = sorted(stats.processed.keys())
        for h in hosts:
            t = stats.summarize(h)
            self.task_status[h] = {
                "ok": t["ok"],
                "changed": t["changed"],
                "unreachable": t["unreachable"],
                "skipped": t["skipped"],
                "failed": t["failed"]
            }

def CallBackPlaybook(playbooks_path,extra_vars={},source=settings.ANSIBLE_SOURCE):
    """
    执行playbook
    :param playbooks_path: playbook的路径 list的类型
    :param source: ansible配置文件hosts
    :return:
    """
    dataloader = DataLoader()
    inventory = InventoryManager(loader=dataloader, sources=source)
    variableManager = VariableManager(loader=dataloader, inventory=inventory)
    variableManager.extra_vars=extra_vars #传入参数
    Options = namedtuple("Options", [
        "connection", "remote_user", "ask_sudo_pass", "verbosity", "ack_pass",
        "module_path", "forks", "become", "become_method", "become_user", "check",
        "listhosts", "listtasks", "listtags", "syntax", "sudo_user", "sudo", "diff"
    ])
    options = Options(connection='ssh', remote_user=None, ack_pass=None, sudo_user=None, forks=settings.ANSIBLE_FORKS, sudo=None,
                      ask_sudo_pass=False,
                      verbosity=5, module_path=None, become=None, become_method=None, become_user=None, check=False,
                      diff=False,
                      listhosts=None, listtasks=None, listtags=None, syntax=None)
    passwords = dict()
    try:
        logger = logging.getLogger("django")
        playbook = PlaybookExecutor(playbooks=playbooks_path, inventory=inventory, variable_manager=variableManager, loader=dataloader, options=options, passwords=passwords)
        callback = PlaybookCallbackBase()
        playbook._tqm._stdout_callback = callback  # 配置callback
        playbook.run()
        logger_info={"playbooks":playbooks_path,"variable_manager":variableManager.get_vars(),"passwords":passwords}
        logger.info(logger_info)
        status_list=['ok','failed','unreachable','skipped','stats']
        result_raw = {"ok": {}, "failed": {}, "unreachable": {}, "skipped": {}, "stats": {}}
        for status in status_list :
            for host,result in getattr(callback,'task_'+status).items() :
                result_raw[status][host] = result._result
                result_raw[status][host]["task"]=result._task.get_name()
        logger.info(str(result_raw))
        result_raw=get_result(result_raw)
        return result_raw
    except Exception as e:
        print(e)
        traceback.print_exc()

if __name__=='__main__':
    import os
    result=CallBackPlaybook([os.path.join(settings.PLAYBOOK_PATHS,'test.yml')],source=settings.ANSIBLE_SOURCE,extra_vars={"user":"TEST"})
    print(result)