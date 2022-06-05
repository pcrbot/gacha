import os
import random
from collections import defaultdict
import re

from hoshino import Service, priv, util
from hoshino.typing import *
from hoshino.util import DailyNumberLimiter, concat_pic, pic2b64, silence

from .. import chara
from .gacha import Gacha
from .update import *
try:
    import ujson as json
except:
    import json

sv_help = '''
[@Bot单抽] 转蛋模拟
[@Bot十连] 转蛋模拟
[@Bot来一井] 3w钻！
[查看卡池] 模拟卡池&出率
[切换卡池] 更换模拟卡池
[氪金@某人] 为某人氪金，恢复抽卡次数
'''.strip()
sv = Service('gacha', help_=sv_help, bundle='pcr娱乐')
jewel_limit = DailyNumberLimiter(15000)
tenjo_limit = DailyNumberLimiter(5)

JEWEL_EXCEED_NOTICE = f'您今天已经抽过{jewel_limit.max}钻了，欢迎明早5点后再来！'
TENJO_EXCEED_NOTICE = f'您今天已经抽过{tenjo_limit.max}张天井券了，欢迎明早5点后再来！'
POOL = ('混合', '日服', '台服', '国服')
DEFAULT_POOL = POOL[0]

_pool_config_file = os.path.expanduser('~/.hoshino/group_pool_config.json')
_group_pool = {}
try:
    with open(_pool_config_file, encoding='utf8') as f:
        _group_pool = json.load(f)
except FileNotFoundError as e:
    sv.logger.warning('group_pool_config.json not found, will create when needed.')
_group_pool = defaultdict(lambda: DEFAULT_POOL, _group_pool)

def dump_pool_config():
    with open(_pool_config_file, 'w', encoding='utf8') as f:
        json.dump(_group_pool, f, ensure_ascii=False)


gacha_10_aliases = ('抽十连', '十连', '十连！', '十连抽', '来个十连', '来发十连', '来次十连', '抽个十连', '抽发十连', '抽次十连', '十连扭蛋', '扭蛋十连', '10连', '10连！', '10连抽', '来个10连', '来发10连', '来次10连', '抽个10连', '抽发10连', '抽次10连', '10连扭蛋', '扭蛋10连')
gacha_1_aliases = ('单抽', '单抽！', '来发单抽', '来个单抽', '来次单抽', '扭蛋单抽', '单抽扭蛋')
gacha_300_aliases = ('抽一井', '来一井', '来发井', '抽发井', '天井扭蛋', '扭蛋天井')

@sv.on_fullmatch(('卡池资讯', '查看卡池', '看看卡池', '康康卡池', '看看up', '看看UP'))
async def gacha_info(bot, ev: CQEvent):
    gid = str(ev.group_id)
    try:
        gacha = Gacha(_group_pool[gid])
    except:
        await bot.finish(ev, f'未知卡池，{POOL_NAME_TIP}', at_sender=True)
    up_chara = gacha.up
    up_chara = map(lambda x: str(
        chara.fromname(x, star=3).icon.cqcode) + x, up_chara)
    up_chara = '\n'.join(up_chara)
    await bot.send(ev, f"本期卡池主打的角色：\n{up_chara}\nUP角色合计={(gacha.up_prob/10):.1f}% 3★出率={(gacha.s3_prob)/10:.1f}%")


POOL_NAME_TIP = '请选择以下卡池\n> 选择卡池 日服\n> 选择卡池 台服\n> 选择卡池 国服\n> 选择卡池 Fes\n> 选择卡池 七冠\n> 选择卡池 联动\n> 选择卡池 限定\n> 选择卡池 混合'
@sv.on_prefix(('切换卡池', '选择卡池'))
async def set_pool(bot, ev: CQEvent):
    #if not priv.check_priv(ev, priv.ADMIN):
    #    await bot.finish(ev, '只有群管理才能切换卡池', at_sender=True)
    name = util.normalize_str(ev.message.extract_plain_text())
    if not name:
        await bot.finish(ev, POOL_NAME_TIP, at_sender=True)
    elif name in ('联动', '活动'):
        await bot.finish(ev,'请选择以下卡池\n环奈、re0、cgss')
    elif name in ('限定'):
        await bot.finish(ev,'请选择以下卡池\n> 选择卡池 夏日限定\n> 选择卡池 万圣节限定\n> 选择卡池 圣诞节限定\n> 选择卡池 新年限定\n> 选择卡池 其他限定')
    elif name in ('夏日限定'):
        await bot.finish(ev,'请选择以下卡池\n水吃、水女仆、水黑、水猫剑、水暴、水电、水狼、水狐、水流、水星、水饺、水望')
    elif name in ('万圣节限定'):
        await bot.finish(ev,'请选择以下卡池\n瓜忍、瓜眼、猫仓唯、鬼裁、瓜狗')
    elif name in ('圣诞节限定'):
        await bot.finish(ev,'请选择以下卡池\n圣千、圣锤、圣克、圣哈、蛋丁')
    elif name in ('新年限定'):
        await bot.finish(ev,'请选择以下卡池\n春田、春猫、春黑、春妈、春吃、春花、春菲、春伊')
    elif name in ('其他限定'):
        await bot.finish(ev,'请选择以下卡池\n情姐、礼妈、富婆、超吃、超猫、怪盗路人妹')
    elif name in ('混合', '混', 'mix'):
        name = '混合'
    elif name in ('日服', '日', 'jp', 'cy', 'cygames'):
        name = '日服'
    elif name in ('台服', '台', 'tw', '搜内', 'sonet'):
        name = '台服'
    elif name in ('国服', '国', 'cn', 'b服', 'b', 'bl', 'bilibili'):
        name = '国服'
    elif name in ('公主祭典', 'fes'):
        name = '公主祭典(Fes)'
    elif name in ('七冠', 'セブンクラウンズ'):
        name = '七冠(セブンクラウンズ)'
    elif name in ('环奈'):
        name = '桥本环奈'
    elif name in ('re0', 're0联动', 're:0联动'):
        name = 'Re：从零开始的异世界生活'
    elif name in ('cgss', 'cgss联动', '偶像大师', '偶像大师联动'):
        name = '偶像大师 灰姑娘女孩 星光舞台'
    elif name in ('贪吃佩可(夏日)', '水吃', '泳装吃货'):
        name = '贪吃佩可(夏日)'
    elif name in ('铃莓(夏日)', '水女仆', '泳装女仆'):
        name = '铃莓(夏日)'
    elif name in ('凯留(夏日)', '水黑', '泳装黑猫'):
        name = '凯留(夏日)'
    elif name in ('珠希(夏日)', '水猫剑', '泳装猫剑'):
        name = '珠希(夏日)'
    elif name in ('铃奈(夏日)', '水暴', '泳装暴击弓'):
        name = '铃奈(夏日)'
    elif name in ('咲恋(夏日)', '水电', '泳装充电宝'):
        name = '咲恋(夏日)'
    elif name in ('真琴(夏日)', '水狼', '泳装狼'):
        name = '真琴(夏日)'
    elif name in ('真步(夏日)', '水狐', '水壶', '泳装狐狸'):
        name = '真步(夏日)'
    elif name in ('流夏(夏日)', '水流', '泳装流夏'):
        name = '流夏(夏日)'
    elif name in ('初音(夏日)', '水星', '海星', '泳装初音'):
        name = '初音(夏日)'
    elif name in ('惠理子(夏日)', '水病', '水饺', '泳装病娇'):
        name = '惠理子(夏日)'
    elif name in ('望(夏日)', '水望', '水偶像', '泳装偶像'):
        name = '望(夏日)'
    elif name in ('忍(万圣节)', '瓜忍', '万圣忍'):
        name = '忍(万圣节)'
    elif name in ('美咲(万圣节)', '瓜眼', '万圣大眼'):
        name = '美咲(万圣节)'
    elif name in ('镜华(万圣节)', '猫仓唯', 'mcw', '万圣小仓唯'):
        name = '镜华(万圣节)'
    elif name in ('纺希(万圣节)', '鬼裁', '万圣裁缝'):
        name = '纺希(万圣节)'
    elif name in ('香织(万圣节)', '瓜狗', '万圣狗'):
        name = '香织(万圣节)'
    elif name in ('千歌(圣诞节)', '圣千', '圣诞千歌'):
        name = '千歌(圣诞节)'
    elif name in ('绫音(圣诞节)', '圣锤', '圣诞熊锤'):
        name = '绫音(圣诞节)'
    elif name in ('克莉丝提娜(圣诞节)', '圣克', '圣诞克总'):
        name = '克莉丝提娜(圣诞节)'
    elif name in ('秋乃(圣诞节)', '圣哈', '圣诞哈哈剑'):
        name = '秋乃(圣诞节)'
    elif name in ('宫子(圣诞节)', '诞丁', '蛋丁', '但丁', '圣诞布丁'):
        name = '宫子(圣诞节)'
    elif name in ('优衣(新年)', '春田'):
        name = '优衣(新年)'
    elif name in ('日和(新年)', '春猫'):
        name = '日和(新年)'
    elif name in ('凯留(新年)', '春黑', '唯一神'):
        name = '凯留(新年)'
    elif name in ('可可萝(新年)', '春妈'):
        name = '可可萝(新年)'
    elif name in ('贪吃佩可(新年)', '春吃'):
        name = '贪吃佩可(新年)'
    elif name in ('似似花(新年)', '春花'):
        name = '似似花(新年)'
    elif name in ('雪菲(新年)', '春菲'):
        name = '雪菲(新年)'
    elif name in ('伊莉亚(新年)', '春伊'):
        name = '伊莉亚(新年)'
    elif name in ('静流(情人节)', '情姐'):
        name = '静流(情人节)'
    elif name in ('可可萝(祭服)', '礼妈', '仪妈'):
        name = '可可萝(祭服)'
    elif name in ('克蕾琪塔', '富婆'):
        name = '克蕾琪塔'
    elif name in ('贪吃佩可(超载)', '超吃'):
        name = '贪吃佩可(超载)'
    elif name in ('凯留(超载)', '超猫'):
        name = '凯留(超载)'
    elif name in ('步未(怪盗)', '怪盗路人妹'):
        name = '步未(怪盗)'
    else:
        await bot.finish(ev, f'未知卡池，{POOL_NAME_TIP}', at_sender=True)
    gid = str(ev.group_id)
    _group_pool[gid] = name
    dump_pool_config()
    await bot.send(ev, f'已切换为{name}卡池', at_sender=True)
    await gacha_info(bot, ev)


async def check_jewel_num(bot, ev: CQEvent):
    if not jewel_limit.check(ev.user_id):
        await bot.finish(ev, JEWEL_EXCEED_NOTICE, at_sender=True)


async def check_tenjo_num(bot, ev: CQEvent):
    if not tenjo_limit.check(ev.user_id):
        await bot.finish(ev, TENJO_EXCEED_NOTICE, at_sender=True)


@sv.on_prefix(gacha_1_aliases, only_to_me=True)
async def gacha_1(bot, ev: CQEvent):

    await check_jewel_num(bot, ev)
    jewel_limit.increase(ev.user_id, 150)

    gid = str(ev.group_id)
    try:
        gacha = Gacha(_group_pool[gid])
    except:
        await bot.finish(ev, f'未知卡池，{POOL_NAME_TIP}', at_sender=True)
    chara, hiishi = gacha.gacha_one(gacha.up_prob, gacha.s3_prob, gacha.s2_prob)
    # silence_time = hiishi * 60

    res = f'{chara.name} {"★"*chara.star}'
    res = f'{chara.icon.cqcode} {res}'

    # await silence(ev, silence_time)
    await bot.send(ev, f'素敵な仲間が増えますよ！\n{res}', at_sender=True)


@sv.on_prefix(gacha_10_aliases, only_to_me=True)
async def gacha_10(bot, ev: CQEvent):
    SUPER_LUCKY_LINE = 170

    await check_jewel_num(bot, ev)
    jewel_limit.increase(ev.user_id, 1500)

    gid = str(ev.group_id)
    try:
        gacha = Gacha(_group_pool[gid])
    except:
        await bot.finish(ev, f'未知卡池，{POOL_NAME_TIP}', at_sender=True)
    result, hiishi = gacha.gacha_ten()
    # silence_time = hiishi * 6 if hiishi < SUPER_LUCKY_LINE else hiishi * 60


    res1 = chara.gen_team_pic(result[:5], star_slot_verbose=False)
    res2 = chara.gen_team_pic(result[5:], star_slot_verbose=False)
    res = concat_pic([res1, res2])
    res = pic2b64(res)
    res = MessageSegment.image(res)
    result = [f'{c.name}{"★"*c.star}' for c in result]
    res1 = ' '.join(result[0:5])
    res2 = ' '.join(result[5:])
    res = f'{res}\n{res1}\n{res2}'


    if hiishi >= SUPER_LUCKY_LINE:
        await bot.send(ev, '恭喜海豹！おめでとうございます！')
    await bot.send(ev, f'素敵な仲間が増えますよ！\n{res}\n', at_sender=True)
    #await silence(ev, silence_time)


@sv.on_prefix(gacha_300_aliases, only_to_me=True)
async def gacha_300(bot, ev: CQEvent):

    await check_tenjo_num(bot, ev)
    tenjo_limit.increase(ev.user_id)

    gid = str(ev.group_id)
    try:
        gacha = Gacha(_group_pool[gid])
    except:
        await bot.finish(ev, f'未知卡池，{POOL_NAME_TIP}', at_sender=True)
    result = gacha.gacha_tenjou()
    up = len(result['up'])
    s3 = len(result['s3'])
    s2 = len(result['s2'])
    s1 = len(result['s1'])

    res = [*(result['up']), *(result['s3'])]
    random.shuffle(res)
    lenth = len(res)
    if lenth <= 0:
        res = "竟...竟然没有3★？！"
    else:
        step = 4
        pics = []
        for i in range(0, lenth, step):
            j = min(lenth, i + step)
            pics.append(chara.gen_team_pic(res[i:j], star_slot_verbose=False))
        res = concat_pic(pics)
        res = pic2b64(res)
        res = MessageSegment.image(res)

    msg = [
        f"\n素敵な仲間が増えますよ！ {res}",
        f"★★★×{up+s3} ★★×{s2} ★×{s1}",
        f"获得记忆碎片×{gacha.memo_pieces*up}与女神秘石×{50*(up+s3) + 10*s2 + s1}！\n第{result['first_up_pos']}抽首次获得up角色" if up else f"获得女神秘石{50*(up+s3) + 10*s2 + s1}个！"
    ]

    if up == 0 and s3 == 0:
        msg.append("太惨了，咱们还是退款删游吧...")
    elif up == 0 and s3 > 7:
        msg.append("up呢？我的up呢？")
    elif up == 0 and s3 <= 3:
        msg.append("这位酋长，梦幻包考虑一下？")
    elif up == 0:
        msg.append("据说天井的概率只有" + gacha.tenjou_rate)
    elif up <= 2:
        if result['first_up_pos'] < 50:
            msg.append("你的喜悦我收到了，滚去喂鲨鱼吧！")
        elif result['first_up_pos'] < 100:
            msg.append("已经可以了，您已经很欧了")
        elif result['first_up_pos'] > gacha.tenjou_line - 10:
            msg.append("标 准 结 局")
        elif result['first_up_pos'] > gacha.tenjou_line - 50:
            msg.append("补井还是不补井，这是一个问题...")
        else:
            msg.append("期望之内，亚洲水平")
    elif up == 3:
        msg.append("抽井母五一气呵成！多出30等专武～")
    elif up >= 4:
        msg.append("记忆碎片一大堆！您是托吧？")

    await bot.send(ev, '\n'.join(msg), at_sender=True)
    #silence_time = (100*up + 50*(up+s3) + 10*s2 + s1) * 1
    #await silence(ev, silence_time)


@sv.on_prefix('氪金')
async def kakin(bot, ev: CQEvent):
    #if ev.user_id not in bot.config.SUPERUSERS:
    #    return
    count = 0
    for m in ev.message:
        if m.type == 'at' and m.data['qq'] != 'all':
            uid = int(m.data['qq'])
            jewel_limit.reset(uid)
            tenjo_limit.reset(uid)
            count += 1
    if count:
        await bot.send(ev, f"已为{count}位用户充值完毕！谢谢惠顾～")
