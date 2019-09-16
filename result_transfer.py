# -*- coding:utf-8 -*-
# CREATE BY Zhou Xiangyu

def get_result(pre_result):
    if isinstance(pre_result,dict) :
        result = _format_result(pre_result)
        #result=dict(filter(lambda x : result[x] is not None ,list(result.keys())))
        for status_res in list(result.keys()) :
            #status_res 为状态failed，unreachable，ok等
            if result[status_res] :
                continue
            else :
                del result[status_res]
        return result
    else :
        raise TypeError

def _format_result(pre_result):
    res={"ok":[],"unreachable":[],"failed":[],"skipped":[],"stats":[]}
    for status in pre_result :
        for ips in pre_result[status] :
            if status == "ok" :
                res[status].append({"ip":ips,"reason":"SUCCESS!","task":pre_result[status][ips]["task"]})
            elif status == "unreachable" :
                res_msg = pre_result[status][ips].get("msg")
                res[status].append({"ip":ips,"reason":res_msg,"task":pre_result[status][ips]["task"]})
            elif status == "skipped" :
                res_msg = pre_result[status][ips].get("skip_reason",None)
                if not res_msg :
                    res_msg = status
                res[status].append({"ip": ips, "reason": res_msg,"task":pre_result[status][ips]["task"]})
            elif status == "failed" :
                reason = pre_result[status][ips].get("stderr",None)
                if not reason :
                    reason = "FAILED!"
                res[status].append({"ip": ips, "reason": reason,"task":pre_result[status][ips]["task"]})
            elif status == "stats" :
                res[status].append({"ip": ips, "reason": status, "task": pre_result[status][ips]["task"]})
                #待重写
    return res
