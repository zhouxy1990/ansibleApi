# -*- coding:utf-8 -*-
# CREATE BY Zhou Xiangyu
#!/usr/bin/env python

from collections import namedtuple
from ansible.parsing.dataloader import DataLoader
from ansible.vars.manager import VariableManager
from ansible.inventory.manager import InventoryManager
from ansible.playbook.play import Play
from ansible.executor.task_queue_manager import TaskQueueManager
from ansible.plugins.callback import CallbackBase
from operation_app import settings
import logging
from result_transfer import get_result
class AdHocCallbackBase(CallbackBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.host_ok = {}
        self.host_unreachable = {}
        self.host_failed = {}
        self.host_skipped={}

    def v2_runner_on_unreachable(self, result):
        """
        重写 unreachable 状态
        :param result:  这是父类里面一个对象，这个对象可以获取执行任务信息
        """
        self.host_unreachable[result._host.get_name()] = result

    def v2_runner_on_ok(self, result, *args, **kwargs):
        """
        重写 ok 状态
        :param result:
        """
        self.host_ok[result._host.get_name()] = result

    def v2_runner_on_failed(self, result, *args, **kwargs):
        """
        重写 failed 状态
        :param result:
        """
        self.host_failed[result._host.get_name()] = result

    def v2_runner_on_skipped(self,result, *args, **kwargs):
        '''
        重写 skipped 状态
        :param result:
        '''
        self.host_skipped[result._host.get_name()]= result

def CallbackBaseAdHoc(hosts,actions,name="Ansible Play",source=settings.ANSIBLE_SOURCE):
    '''
    :param hosts: 主机列表
    :param actions: 相关ad-hoc的指令，以字典形式 [dict(action=dict(module="shell", args="touch /tmp/bbb.txt", warn=False)),]
    :param name: 任务名称
    :param source ansible配置hosts文件
    :return:
    '''
    logger=logging.getLogger("django")
    dataLoader = DataLoader()
    inventory = InventoryManager(loader=dataLoader, sources=source) #主机信息管理
    variableManager = VariableManager(loader=dataLoader, inventory=inventory) #变量管理
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
    play_source = dict(name=name,  # 任务名称
                       hosts=hosts,  # 目标主机，可以填写具体主机也可以是主机组名称
                       gather_facts="no",  # 是否收集主机配置信息
                       tasks=actions # tasks是具体执行的任务，列表形式，每个具体任务都是一个字典
                       )
    play = Play().load(play_source, variable_manager=variableManager, loader=dataLoader)
    passwords = dict()  # 这个可以为空，因为在hosts文件中有配置或者密钥登陆
    callback = AdHocCallbackBase()

    tqm = TaskQueueManager(
        inventory=inventory,
        variable_manager=variableManager,
        loader=dataLoader,
        options=options,
        passwords=passwords,
        stdout_callback=callback
    )
    logger_info={"hosts":hosts,
                 "actions":actions,
                 "passwords":passwords}
    logger.info(str(logger_info))
    tqm.run(play)
    status_list = ['ok', 'failed', 'unreachable','skipped']
    result_raw = {"failed": {}, "unreachable": {},"ok":{},"skipped":{}}
    for status in status_list:
        for host, result in getattr(callback, 'host_' + status).items():
            result_raw[status][host] = result._result
            result_raw[status][host]["task"] = name
    logger.info(str(result_raw))
    result_raw=get_result(result_raw)
    return result_raw

if __name__=='__main__':
    actions=[dict(action=dict(module="shell", args="touch /tmp/bbb.txt", warn=False)),]
    CallbackBaseAdHoc(['123.123.123.123',],actions,name='Ansible test',source=settings.ANSIBLE_SOURCE)
'''
[dict(action=dict(module="shell", args="touch /tmp/bbb.txt", warn=False)),]
'''