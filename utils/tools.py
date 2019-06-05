from calculate.calculate import Calculator


def get_qb_score(key, client):
    """获取全部成绩"""
    jg_score = list(client.jg[key].find({'学期': {'$regex': '学期.*'}}))  # 查询及格成绩
    bjg_score = list(client.bjg[key].find({'类型': 'sbjg'}))  # 查询尚不及格成绩
    if not jg_score:
        return {'error_message': '暂无数据可进行分析,请先查询成绩!'}
    jg_score.extend(bjg_score)  # 合并成绩
    return jg_score


def get_point(key, client, school=None):
    """获取绩点"""
    scores = get_qb_score(key, client)
    if school is None:
        school = 'zb'
    if isinstance(scores, dict):
        return scores
    cal = Calculator(scores)
    current_point = cal.average(school=school)
    return current_point
