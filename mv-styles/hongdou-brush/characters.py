# -*- coding: utf-8 -*-
"""
《红豆》手绘版 · 人物：她（girl）和他（boy）。只通过 Pen 指令作画（cover/fill/shade/line/hatch/dot/light/lift），
不碰任何笔刷；三种笔刷下几何完全一样，笔刷只换材质。比例统一用修长的 6 头身。

━━ 公共约定 ━━
  坐标：场景像素坐标（y 向下）。人物以“颈根”（两锁骨中点）定位，s = 头高（头顶到下巴，不含头发，像素）。
  身体局部坐标 (u, v)：u 指向人物朝向的前方，v 向下，单位 = s，原点 = 颈根。
  头部是一个很小的 2.5D 模型：头是一圈圈水平椭圆截面，头发是套在外面的发壳，按 yaw/pitch/roll 旋转后
  用画家算法（按深度）决定 头发 / 脸 / 耳朵 / 脖子 / 高领 谁挡谁，结果作为遮罩交给 pen.cover / pen.fill。
  语义：固有色用 fill（skin 皮肤、hair 头发、sweater 毛衣…），光影用 shade（朝背光一侧、头发投在额头上的影、
  下巴投在脖子上的影），高光用 lift（头发光泽、眼睛高光）。线：轮廓 role='contour'，衣褶/发丝 role='detail'，
  五官 role='feature'，他的草稿 role='sketch'/'construct'。

━━ 表情 ━━
  EXPR / expr(name) / mix_expr(a, b, t)。每个表情是参数 dict：
    open 睁眼 0..1.2（<0.18 视为闭眼；黑眼珠固定在眼眶里，open 小 = 上眼皮放下来盖住黑眼珠上半，眼神柔和）
    gx/gy 视线（gy>0 往下看）  smile 嘴角 -1..1  brow 眉头上扬（愁）  brow_out 眉尾下垂（温柔/难过）
    brow_y 整条眉上抬  mouth_open 张嘴 0..1  tear 眼泪 0..1（沿脸颊流下的进度）  happy 笑眼（睁眼时下眼睑上推，
    闭眼时 ∩ 形弯眼）  pucker 嘟嘴（亲吻）  blush 腮红 0..1  wet 眼里含光 0..1（黑眼珠下半透亮、下方高光更亮）
  名字：neutral smile wistful_smile（想念的浅笑：微眯、半垂眼皮、含光、眉尾微垂）sad_down blink surprise laugh
        cry closed_smile kiss_close gentle

━━ 她 girl(pen, pose, parts=None) -> info ━━
  pose 字典：
    x, y        颈根场景坐标             s 头高（像素）          facing 1=朝右 / -1=朝左（发夹始终在她自己的同一侧，见 PIN_SIDE）
    yaw         头转向（度）：0=正对镜头，>0 转向朝向一侧，90=纯侧面，180=后脑
    pitch       >0 低头          roll   >0 头顶往朝向一侧歪
    face        表情名或参数 dict（mix_expr 的结果）；blink 0..1 叠加眨眼
    breath      呼吸相位（周期 1）    lean  上身前倾（以臀部为轴，>0 朝前，常用 0..0.3）
    body        'upper'（默认，画到臀部，配合 clip_y 被台面挡住）/'stand'（全身站立：长裙、腿、鞋）/'sit'（坐姿）
    clip_y      身体在这条水平线以下被前景挡住（台面后沿、桌面）；clip_poly 可见区域多边形（更一般，二者可同时用）
    arm         手臂姿态名（ARM_POSES 的键）；arm_t 时间（秒）；arm_args 该姿态的参数 dict（见各 arm_xxx 的说明）
    sit_y       坐姿时椅面（臀底）的 y；不写 = y + 1.62 s
    gait, step  走路相位（周期 1）与步幅 0..1（body='stand' 时腿前后摆；预留，粗略可用）
    clip_arms   False = 手臂不被 clip_y/clip_poly 裁（坐在桌前、前臂搁在桌面上时用）
    back        背影：True 时画背面的身体（facing 不起作用，人物自己的右侧在画面右边），头默认 yaw=180，
                不画五官；body='stand'（窗前站着：长裙、小腿、鞋跟）/'ground'（坐在草地上，腿伸向前方被身体挡住）；
                tilt 度：上身以臀部为轴往画面右侧歪（负 = 左）；roll 头往一侧倒；yaw 180±20 头略转。
                手臂：arm='hold_line'（一只手在胸前高度攥着红线）或不写（站：两手自然垂下；坐：撑在身边草地上）。
                返回 info['hand']（攥红线的拳头）、info['hands']、info['neck']、info['head_c']。
    light       光从哪侧来：1 = 朝向一侧（默认）、-1 = 身后一侧
    seed        个体种子（同一个人固定）    boil  画层抖动（默认 1.0）    group  True=自己开画层（默认）
  parts：None = 全画；或 {'body', 'head', 'arm'} 的子集。场景要在“身体/头”和“近侧手臂”之间插入东西（锅里的汤）时，
         先 girl(pen, pose, {'body','head'})，画汤，再 girl(pen, pose, {'arm'})。
  返回 info：hand 近侧手位置、tool_tip 勺尖、eye (近侧眼, 远侧眼)、chin 下巴、head_c 头中心、sil 剪影多边形列表。
  girl_silhouette(pose) 只算剪影（给场景做“留白”光晕用），不画。
  发型：齐刘海（下沿手绘参差 + 几缕分叉）、两侧鬓发；红豆发夹别在耳朵上方（PIN_SIDE，默认她自己的右侧——
  厨房里她朝右，发夹在近侧看得见）。发夹那一侧头发别在耳后露出耳朵，另一侧短 bob 盖住耳朵。

  第 5 镜 · 坐在桌前的侧面近景（低头看碗、手扶碗沿、流泪）：
      girl(pen, dict(x, y, s, facing=1, yaw≈48, pitch≈30, roll≈5, lean≈0.3, face='cry', clip_y=桌面后沿,
                     clip_arms=False, arm='bowl_rim', arm_args=dict(bowl=(cx,cy), r=碗口半径, u=0..1)))
      bowl(pen, (cx,cy), r)                     画碗（红豆汤），先于她画
      girl_tear_point(pose, pen=None, where='eye'|'end')  泪滴起点（近侧眼睛下方 / 泪痕下端）的场景坐标；给 pen 返回屏幕坐标
      tear_drop(pen, x, y, size, seed, stretch) 场景自己画“正在落下的那一颗泪”（size≈0.045 s，stretch 下落时拉长）
      yaw 超过 ~55° 时这个头部模型没有鼻梁/嘴唇的侧面剪影，侧面近景建议 yaw 40–55。
  第 16 镜/T3 · 窗前背影：girl(pen, dict(x, y, s, back=True, body='stand', arm='hold_line',
                     arm_args=dict(side='right', tug=0..1, hand=可省)))，红线从 info['hand'] 画出去。
  第 17/19 镜 · 并肩坐草地背影：pair_sit_back(pen, dict(x, y, s, lean=0..1, boy_mode='full'|'sketch', ...))（见函数说明）。
  第 7 镜（预留，只留了接口）· 他低头亲她额头：她 body='stand', facing=1, yaw≈70, pitch≈-10, face='closed_smile'；
      他 pose='stand', facing=-1, yaw≈70, pitch≈28, face='kiss_close'；用 girl_forehead_point(她的 pose) 和
      boy_mouth_point(他的 pose) 对位（调他的 x,y 让两点重合）。他抱她的手臂姿态还没做。

━━ 手臂姿态 ARM_POSES ━━
  每个姿态 fn(t, args, rig) -> dict(near=手臂描述, far=手臂描述或 None)。手臂描述：
    hand 手（掌心中点）位置；shape 'fist'|'open'|'flat'|'cup'；front 远侧手臂是否在身体前面；bend 肘的弯向；
    tool ('spoon', 勺尖) / ('bowl', 中心, 半径) / ('cup', 中心, 高)；thumb 拇指在哪侧。
  stir(soup=(cx,cy,rx,ry), period, t0, handle)  搅锅      rest(hand)                       手搭在台面/桌上
  reach(start, target, u)                        伸手      wipe_tear(eye 可省, u)           手指背擦泪
  hold(at, r, what='bowl'|'cup')                 双手捧碗  hug_self()                       抱臂
  hand_chest(u)                                  手按胸口  spoon_bowl(bowl=(cx,cy), lift)   坐着用勺舀碗里的汤
  bowl_rim(bowl=(cx,cy), r, u, rest)             手扶碗沿（侧面近景）
  hold_line(side='right', tug, hand)             背影专用：一只手在胸前高度攥着红线，另一只垂下/撑地
  新姿态 = 写一个函数注册进 ARM_POSES。

━━ 他 boy(pen, pose, mode='sketch'|'full') -> info ━━
  同一套修长比例，比她高半个头（同距离下 s 取她的 1.08 倍左右）。pose 字典：
    x, y, s, facing(默认 -1), yaw(36), pitch(-6), roll(7), face(表情名/参数；常用 neutral/smile/closed_smile/gentle)
    pose        'sit_chin'（坐着一手托腮，另一前臂平放桌上）/'stand'/'sit_eat'（坐着双手捧碗）
                /'ground'（坐在草地上，只用于背影）
    back        背影（同她：facing 不起作用；pose='stand'/'ground'；tilt、roll、yaw≈180）。
                arm_near / arm_far 可覆盖手臂（dict(hand=场景坐标, shape, straight=True) 或 dict(hang=True)）。
                返回 info['hands']、info['shoulders']（near = 他自己的右侧 = 画面右）。
    elbow, elbow2, hand2   sit_chin 时托腮手肘、近侧手肘、近侧手的位置（场景坐标，可省）
    bowl        sit_eat 时碗的中心（可省）
    clip_y / clip_poly     桌面挡住身体（只裁身体，不裁搁在桌上的手臂）
    erase       0..1 被擦掉的程度（线断开 breaks、出现橡皮擦痕）
    opacity     sketch 模式画层透明度（默认 0.6）    boil  抖动（sketch 默认 2.1，full 默认 1.0）
    seed, breath, light, group 同她
  mode='sketch'：未完成的铅笔草稿：起形辅助线（头部椭圆+十字中线、脊柱动势线、肩线）role='construct'，
                 轮廓 role='sketch'（reps 重复描、spread 离散），不上色；整个人在 group(knock=False, opacity≈0.6, boil≈2.1) 里。
  mode='full'  ：同一套轮廓点，加固有色（boy_hair/boy_shirt/boy_sweater/boy_pants/skin）、阴影、五官。

━━ 追加（cast3：第 3/4/6/7/8/15 镜）━━ 代码在文件末尾“追加（cast3）”一节，每个函数的说明里有全部参数；
  scenes/_castsheet2.py 是每个姿势的用法示例（python preview.py _castsheet2 C 0 out.png kind=serve u=0.7）。
  新表情：eat（被喂：笑眼眯着、嘴微张、脸红）resolve（含泪但眼神坚定：眼里泪光 wet + 一点泪痕、眉微蹙压低、嘴抿着、
          下眼睑微绷）peace（安心地闭眼 ‿）blow（嘟嘴吹凉、垂眼看勺子）distant（出神地望向远处）
  她的新手臂姿态（girl 的 arm / arm_args；坐标都是场景坐标）：
    ladle(pot, bowl, r, u, steady)    盛汤：近侧手握长柄木汤勺。u 0–0.28 在锅里舀 → 0.55 端到碗上方 → 0.55–0.90 倾倒（勺斗前倾，
                                      红豆汤从前沿流进碗里，near['pour'] 倾倒量）→ 1 收回；远侧手扶着小碗（steady=False 不扶）
    push(bowl, to, r, u)              推碗：近侧手指搭在碗沿后侧、手掌推着碗往前滑；碗位置 = lerp(bowl, to, smooth01(u))
    place(spoon, to, u, lift, soup)   摆勺子：近侧手捏着金属汤勺从 spoon（勺头中心）移到 to
    catch(u, chin, rest)              被喂时近侧手掌心朝上接在下巴下面
    fist_chest(u, grip, press, rest, chest, bean)  攥着红豆按在胸口：u 抬手；grip<0.5 摊开的掌心里躺着红豆，≥0.5 握拳、
                                      拳缝露出一点红；press 往胸口按
    back_table(spread)                背影（back=True, body='sit'）：两前臂往前搁在桌上，只露出上臂和肘
  带道具的姿态（ladle、place 的勺子、fist_chest 的红豆）要用下面两个函数画手臂，girl() 自己只画手不画这些道具：
    girl_with(pen, pose, props)       身体+头 → props(pen)（场景画锅、碗）→ 两只手臂（手压在碗上）。第 3 镜用它。
    girl_arms(pen, pose, which)       只画手臂（含道具）；配合 girl(pen, dict(pose, arm=None), parts=('body','head')) 自己排层。
  girl_front(pen, pose, parts)        第 15 镜：正面（yaw 0–35）上半身，左右对称的身体；pose 同 girl()，另有 body_yaw；
                                      arm 用 fist_chest（拳头在身前）；不写 arm = 两手垂下被桌面挡住。
  girl_mouth_point(pose)              她嘴的场景坐标（喂汤对位）
  过肩背影（第 4 镜）：girl(pen, dict(x, y, s≈300, back=True, body='sit', yaw≈150（转一点，露出右耳上方的红豆发夹）,
                     pitch, roll, arm='back_table'))，下半身让画框切掉。
  站着按胸口望门（第 8 镜）：girl(pen, dict(body='stand', facing, yaw, pitch, arm='hand_chest', arm_args=dict(u),
                     face=mix_expr('sad_down', dict(EXPR['sad_down'], gx=…, gy=…), t)))；眼睛用 gx/gy 跟着他，头用 yaw/pitch 跟。
  boy_act(pen, pose, mode)            他的动作（sketch/full 同一套几何）：act='reach' 坐着伸手够桌上的勺子（target 指尖点、u）/
                                      'feed' 坐着拿汤勺喂她（target=她的嘴、u：0 自己嘴边吹凉 → 1 她嘴边、bowl 他自己的碗）/
                                      'rise' 从椅子上站起（rise、floor、table）/'walk' 走路（gait、step、back）/
                                      'door' 背对镜头开门（handle、u）/'stand'；arm_near / arm_far 覆盖手臂；
                                      dust 0..1 草稿从指尖（dust_from）开始化成灰、顺 wind 飘散。坐姿时桌面后沿约在颈根下 1.1–1.2 s。
  couple(pen, pose) / couple_poses(pose)  第 7 镜 + T2 窗边两人：k 他低头亲她额头（自动对位）/ look_up 她睁眼抬头看他 /
                                      hug 她把脸靠在他胸口、他双臂环住她 / look_away 他转头望向窗外 / loosen 手臂松开垂下。
"""
import math
from contextlib import contextmanager

import cv2
import numpy as np

from core import spline, ell, bez, densify, tube, ik2, rng, sd, clamp, smooth01, lerp, W, H

try:
    from shapely.geometry import Polygon as _SPoly
    from shapely.validation import make_valid as _make_valid
except Exception:      # pragma: no cover
    _SPoly = None

# 标签（画家算法）
_HAIR, _FACE, _NECK, _EAR, _COLLAR = 1, 2, 3, 4, 5

SHOE = '#4A3A36'      # 她的平底鞋（PAL 里没有，先用十六进制）
TIGHTS = '#4B4552'    # 冬天的深色袜
BOY_SHOE = '#3B3230'
MOUTH_IN = '#9A5552'
EYE_WHITE = '#FBF8F3'


# =========================================================================== 表情
def _E(**kw):
    base = dict(open=0.80, gx=0.10, gy=0.30, smile=0.06, brow=0.05, brow_y=0.0, brow_out=0.0, mouth_open=0.0,
                tear=0.0, happy=0.0, pucker=0.0, blush=0.45, wet=0.0)
    base.update(kw)
    return base


EXPR = {
    'neutral':       _E(open=0.72, brow=0.14),
    'smile':         _E(open=0.78, gy=0.05, smile=0.70, brow=-0.05, happy=0.40, blush=0.60),
    # 想念的浅笑：眼睛微眯、上眼皮放松半垂、眼里含光（wet），眉尾微垂，嘴角浅浅上扬
    'wistful_smile': _E(open=0.56, gx=0.30, gy=0.0, smile=0.42, brow=0.28, brow_out=0.55, happy=0.40, blush=0.55,
                        wet=1.0),
    'sad_down':      _E(open=0.36, gx=0.05, gy=0.85, smile=-0.28, brow=0.70, brow_out=0.35, blush=0.35, wet=0.5),
    'blink':         _E(open=0.0, gy=0.20, smile=0.0, brow=0.10),
    'surprise':      _E(open=1.10, gx=0.0, gy=-0.10, smile=0.0, brow=0.10, brow_y=1.0, mouth_open=0.50, blush=0.30),
    'laugh':         _E(open=0.0, gy=0.0, smile=1.0, brow=-0.10, brow_y=0.30, mouth_open=0.55, happy=1.0, blush=0.85),
    'cry':           _E(open=0.42, gx=0.0, gy=0.50, smile=-0.55, brow=0.95, brow_out=0.40, mouth_open=0.10, tear=1.0,
                        blush=0.75, wet=1.0),
    'closed_smile':  _E(open=0.0, gy=0.10, smile=0.62, brow=0.0, happy=1.0, blush=0.70),
    'kiss_close':    _E(open=0.0, gy=0.30, smile=0.10, brow=0.15, pucker=1.0, blush=0.80),
    'gentle':        _E(open=0.66, gx=0.25, gy=0.05, smile=0.40, brow=0.15, happy=0.35, blush=0.40, wet=0.4),
}


def expr(name):
    return dict(EXPR[name])


def mix_expr(a, b, t):
    a = EXPR[a] if isinstance(a, str) else a
    b = EXPR[b] if isinstance(b, str) else b
    t = float(min(max(t, 0.0), 1.0))
    keys = set(a) | set(b)
    base = EXPR['neutral']
    return {k: a.get(k, base.get(k, 0.0)) * (1 - t) + b.get(k, base.get(k, 0.0)) * t for k in keys}


def _face_of(f):
    if f is None:
        return dict(EXPR['neutral'])
    if isinstance(f, str):
        return dict(EXPR[f])
    e = dict(EXPR['neutral'])
    e.update(f)
    return e


# =========================================================================== 小工具
def _noise1(u, seed, freq=4, octaves=2):
    """周期为 1 的一维值噪声（发梢不齐、发壳起伏）。"""
    u = np.asarray(u, np.float64)
    r = rng(seed, 77)
    out = np.zeros_like(u)
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        n = int(freq * 2 ** o)
        g = r.standard_normal(n)
        xp = np.arange(n + 1) / n
        fp = np.concatenate([g, g[:1]])
        out += amp * np.interp(u % 1.0, xp, fp)
        tot += amp
        amp *= 0.5
    return (out / tot).astype(np.float32)


def _unit(v):
    v = np.asarray(v, np.float32)
    return v / (float(np.linalg.norm(v)) + 1e-6)


def _perp(v):
    return np.float32([-v[1], v[0]])


@contextmanager
def _screen(pen):
    """在这个上下文里 pen 的取景是恒等变换：用来交出已经在屏幕坐标里栅格化好的遮罩（特写时不糊）。"""
    s = pen.scale
    o = pen.to_screen(np.zeros((1, 2), np.float32))[0]
    if abs(s - 1.0) < 1e-9 and abs(o[0]) < 1e-6 and abs(o[1]) < 1e-6:
        yield pen
        return
    with pen.view(1.0 / s, -float(o[0]) / s, -float(o[1]) / s):
        yield pen


class _Clipper:
    """身体被前景挡住：clip_y（水平线以上可见）和/或 clip_poly（可见区域）。多边形用 shapely 求交，线按点切段。"""

    def __init__(self, clip_y=None, clip_poly=None):
        self.y = None if clip_y is None or clip_y >= H + 2000 else float(clip_y)
        self.poly = None if clip_poly is None else np.asarray(clip_poly, np.float32)
        self.active = self.y is not None or self.poly is not None
        self._sp = None
        if self.active and _SPoly is not None:
            big = 1e5
            geo = None
            if self.y is not None:
                geo = _SPoly([(-big, -big), (big, -big), (big, self.y), (-big, self.y)])
            if self.poly is not None:
                p = _make_valid(_SPoly(self.poly))
                geo = p if geo is None else geo.intersection(p)
            self._sp = geo

    def inside(self, P):
        P = np.asarray(P, np.float32).reshape(-1, 2)
        ok = np.ones(len(P), bool)
        if self.y is not None:
            ok &= P[:, 1] <= self.y
        if self.poly is not None:
            ok &= np.array([cv2.pointPolygonTest(self.poly, (float(x), float(y)), False) >= 0 for x, y in P], bool)
        return ok

    def polys(self, polys):
        if not self.active or self._sp is None:
            return polys
        out = []
        for p in polys:
            p = np.asarray(p, np.float32).reshape(-1, 2)
            if len(p) < 3:
                continue
            if self.y is not None and self.poly is None and p[:, 1].max() <= self.y:
                out.append(p)
                continue
            try:
                g = _make_valid(_SPoly(p)).intersection(self._sp)
            except Exception:
                continue
            for q in getattr(g, 'geoms', [g]):
                if q.geom_type == 'Polygon' and q.area > 1.0:
                    out.append(np.asarray(q.exterior.coords, np.float32)[:-1])
                elif q.geom_type in ('MultiPolygon', 'GeometryCollection'):
                    for qq in q.geoms:
                        if qq.geom_type == 'Polygon' and qq.area > 1.0:
                            out.append(np.asarray(qq.exterior.coords, np.float32)[:-1])
        return out


def _sk(seed, k):
    """种子 + 段号（展平成 core 能接受的元组）。"""
    if isinstance(seed, (tuple, list)):
        return tuple(seed) + (k,)
    return (seed, k)


def _runs(P, ok, min_pts=3):
    """布尔数组切段 → [(起点, 终点(不含), 起点被切, 终点被切)]。"""
    out = []
    n = len(ok)
    i = 0
    while i < n:
        if not ok[i]:
            i += 1
            continue
        j = i
        while j < n and ok[j]:
            j += 1
        if j - i >= min_pts:
            out.append((i, j, i > 0, j < n))
        i = j
    return out


# =========================================================================== 画线（带裁切）
class _Ink:
    """一个人物的作画助手：线、多边形都先经过 clip（被台面挡住）和遮罩裁切（被头发挡住）。"""

    def __init__(self, pen, S, clip=None, role_map=None, breaks=0.0, sketch=False):
        self.pen = pen
        self.S = S
        self.clip = clip
        self.role_map = role_map or {}
        self.breaks = breaks
        self.sketch = sketch

    def line(self, pts, w, tone=0.85, seed=0, role='contour', color=None, closed=False, taper=(0.12, 0.30),
             clip=True, keep=None, spacing=None, **hints):
        """keep: 可选函数 (屏幕上不需要) 场景点 -> bool 数组，False 的点不画（被头发挡住等）。"""
        P = np.asarray(pts, np.float32).reshape(-1, 2)
        if len(P) < 2:
            return
        role = self.role_map.get(role, role)
        if self.breaks > 0 and 'breaks' not in hints:
            hints['breaks'] = self.breaks
        if self.sketch and role == 'sketch':
            hints.setdefault('reps', 2)
            hints.setdefault('spread', 1.8)
        need = (clip and self.clip is not None and self.clip.active) or keep is not None
        if not need:
            self.pen.line(P, w, tone=tone, color=color, seed=seed, closed=closed, taper=taper, role=role, **hints)
            return
        sp = spacing or max(3.0, self.S * 0.03)
        if closed:
            P = np.vstack([P, P[:1]])
        D = spline(P, sp, False) if len(P) > 2 else densify(P, sp)
        ok = np.ones(len(D), bool)
        if clip and self.clip is not None and self.clip.active:
            ok &= self.clip.inside(D)
        if keep is not None:
            ok &= keep(D)
        if ok.all():
            self.pen.line(P[:-1] if closed else P, w, tone=tone, color=color, seed=seed, closed=closed,
                          taper=taper, role=role, **hints)
            return
        for k, (a, b, ca, cb) in enumerate(_runs(D, ok)):
            seg = D[a:b]
            step = max(1, len(seg) // 24)
            seg = np.vstack([seg[::step], seg[-1:]]) if step > 1 else seg
            tp = (0.02 if ca else taper[0], 0.02 if cb else taper[1])
            self.pen.line(seg, w, tone=tone, color=color, seed=_sk(seed, k), closed=False, taper=tp, role=role,
                          **hints)

    def polys(self, polys):
        polys = [np.asarray(p, np.float32) for p in polys if p is not None and len(p) >= 3]
        if self.clip is not None and self.clip.active:
            polys = self.clip.polys(polys)
        return polys

    def cover(self, polys, seed=0, **kw):
        P = self.polys(polys)
        if P:
            self.pen.cover(P, seed=seed, **kw)

    def fill(self, polys, color, seed=0, **kw):
        P = self.polys(polys)
        if P:
            self.pen.fill(P, color, seed=seed, **kw)

    def shade(self, polys, amount=0.3, seed=0, **kw):
        P = self.polys(polys)
        if P:
            self.pen.shade(P, amount=amount, seed=seed, **kw)

    def hatch(self, polys, angle, spacing, seed=0, **kw):
        P = self.polys(polys)
        if P:
            self.pen.hatch(P, angle=angle, spacing=spacing, seed=seed, **kw)

    def lift(self, polys, amt=1.0, seed=0, **kw):
        P = self.polys(polys)
        if P:
            self.pen.lift(P, amt=amt, seed=seed, **kw)


# =========================================================================== 头部 2.5D
class HeadProj:
    """头部局部坐标（单位=头高 S，y 向下，z 朝镜头，x 在正面朝镜头时指向画面右侧）→ 场景坐标。
    pivot 是颈顶（头绕此点转动）在场景中的位置；flip=-1 时整体镜像（朝左）。"""

    def __init__(self, pivot, S, yaw, pitch, roll, flip=1, piv=(0.0, 0.34, -0.06)):
        self.pivot = np.float32(pivot)
        self.yaw = yaw
        self.S = float(S)
        self.flip = flip
        y, p = math.radians(yaw), math.radians(pitch)
        cy, sy, cp, sp = math.cos(y), math.sin(y), math.cos(p), math.sin(p)
        Rp = np.array([[1, 0, 0], [0, cp, sp], [0, -sp, cp]], np.float32)
        Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]], np.float32)
        self.R = Ry @ Rp
        self.piv = np.float32(piv)
        a = math.radians(roll) * flip
        self.ca, self.sa = math.cos(a), math.sin(a)

    def rot(self, P):
        return (np.asarray(P, np.float32) - self.piv) @ self.R.T

    def __call__(self, P, with_z=False):
        Q = self.rot(P)
        x, y = Q[..., 0] * self.flip, Q[..., 1]
        xs = x * self.ca - y * self.sa
        ys = x * self.sa + y * self.ca
        out = np.stack([self.pivot[0] + self.S * xs, self.pivot[1] + self.S * ys], -1).astype(np.float32)
        if with_z:
            return out, Q[..., 2]
        return out


def _rings(ys, hw, fr, bk, nphi):
    """截面环 → 网格点 (ny, nphi, 3)。phi=90° 是正前方。"""
    ph = np.linspace(0, 2 * math.pi, nphi + 1)[:-1] + math.pi / nphi
    ys, hw, fr, bk = (np.asarray(a, np.float32)[:, None] for a in (ys, hw, fr, bk))
    zc, hd = (fr + bk) / 2, (fr - bk) / 2
    X = hw * np.cos(ph)[None, :]
    Z = zc + hd * np.sin(ph)[None, :]
    Y = np.repeat(ys, nphi, 1)
    return np.stack([X, Y, Z], -1).astype(np.float32), ph


def _resample(tab_y, cols, n):
    yy = np.linspace(tab_y[0], tab_y[-1], n)
    return [yy] + [np.interp(yy, tab_y, c) for c in cols]


def _quads(G):
    """网格 (nj, ni, ...) → 四边形顶点索引用的四个角 (nj-1, ni, 4, ...)（环向首尾相接）。"""
    G1 = np.roll(G, -1, axis=1)
    return np.stack([G[:-1], G1[:-1], G1[1:], G[1:]], 2)


def _normals(Q3):
    """四边形（旋转后的 3D 坐标，(…, 4, 3)）的法线（朝外：与“中心 - 头心”同向）。"""
    a = Q3[..., 1, :] - Q3[..., 0, :]
    b = Q3[..., 3, :] - Q3[..., 0, :]
    n = np.cross(a, b)
    n /= (np.linalg.norm(n, axis=-1, keepdims=True) + 1e-6)
    return n


# 她的脸型（年轻、柔和：脸颊下半略饱满，下颌圆顺地收到小而圆的下巴，下巴不长）
_FY = [-0.5, -0.45, -0.38, -0.28, -0.16, -0.04, 0.06, 0.16, 0.25, 0.33, 0.39, 0.435, 0.47]
_FW = [0.05, 0.19, 0.27, 0.33, 0.355, 0.362, 0.360, 0.350, 0.326, 0.288, 0.232, 0.160, 0.060]
_FF = [0.0, 0.16, 0.27, 0.35, 0.39, 0.41, 0.42, 0.42, 0.405, 0.385, 0.358, 0.325, 0.290]
_FB = [-0.05, -0.22, -0.34, -0.42, -0.45, -0.45, -0.42, -0.35, -0.25, -0.14, -0.06, 0.02, 0.09]
# 他的脸型（下颌略方，下巴略宽）
_BY = [-0.5, -0.46, -0.4, -0.32, -0.22, -0.1, 0.0, 0.1, 0.19, 0.27, 0.34, 0.41, 0.46, 0.50]
_BW = [0.03, 0.17, 0.26, 0.32, 0.355, 0.365, 0.365, 0.36, 0.348, 0.325, 0.290, 0.228, 0.150, 0.06]
_BF = [0.0, 0.15, 0.26, 0.34, 0.39, 0.41, 0.42, 0.42, 0.41, 0.39, 0.37, 0.34, 0.31, 0.28]
_BB = [-0.05, -0.22, -0.34, -0.43, -0.46, -0.46, -0.43, -0.36, -0.26, -0.15, -0.06, 0.03, 0.09, 0.12]
# 她：齐肩短发的发壳
_RY = [-0.565, -0.5, -0.42, -0.3, -0.18, -0.06, 0.05, 0.2, 0.35, 0.5, 0.62, 0.72, 0.80]
_RW = [0.04, 0.21, 0.32, 0.39, 0.415, 0.42, 0.415, 0.405, 0.40, 0.41, 0.43, 0.45, 0.46]
_RF = [0.0, 0.18, 0.31, 0.40, 0.445, 0.46, 0.41, 0.36, 0.30, 0.23, 0.18, 0.15, 0.14]
_RB = [-0.06, -0.27, -0.40, -0.49, -0.53, -0.53, -0.50, -0.43, -0.35, -0.28, -0.25, -0.24, -0.24]
BANG_G = -0.080      # 她的刘海下沿（正中；刚好露出眉毛）
PIN_SIDE = 'right'   # 红豆发夹别在她自己的哪一侧（耳朵上方）。'right'：厨房（朝右）里在近侧、看得见
# 他：短发
_SY = [-0.60, -0.55, -0.47, -0.37, -0.25, -0.12, 0.0, 0.12, 0.24]
_SW = [0.05, 0.22, 0.32, 0.385, 0.405, 0.405, 0.392, 0.37, 0.345]
_SF = [0.0, 0.20, 0.33, 0.42, 0.46, 0.47, 0.45, 0.40, 0.33]
_SB = [-0.08, -0.29, -0.43, -0.51, -0.54, -0.53, -0.49, -0.41, -0.33]


def _surf(tab, y, phi, sc=1.0, dz=0.0):
    """脸部蛋形表面上的点。y 高度（单位头高，向下为正），phi=0 正前方，phi>0 朝 +x，度。"""
    TY, TW, TF, TB = tab
    y = np.asarray(y, np.float32)
    phi = np.asarray(phi, np.float32)
    y, phi = np.broadcast_arrays(y, phi)
    hw = np.interp(y, TY, TW) * sc
    fr = np.interp(y, TY, TF) * sc
    bk = np.interp(y, TY, TB) * sc
    zc, hd_ = (fr + bk) / 2, (fr - bk) / 2
    a = np.radians(90.0 - phi)
    return np.stack([hw * np.cos(a), y, zc + hd_ * np.sin(a) + dz], -1).astype(np.float32)


GIRL_FACE = (_FY, _FW, _FF, _FB)
BOY_FACE = (_BY, _BW, _BF, _BB)


def _girl_hair_low(seed, phh, ts=1):
    """她每一列头发（方位 phh）的下沿 y：齐刘海（参差 + 几处分叉）→
    发夹一侧（模型 x 符号 ts）：细细一绺鬓发（发梢收尖）→ 别到耳后（露出耳朵）→ 后面；
    另一侧：短 bob 盖住耳朵垂到下颌（发梢一绺一绺）。"""
    u = phh / (2 * math.pi)
    fch = (phh - math.pi / 2 + math.pi) % (2 * math.pi) - math.pi
    fd = np.degrees(fch)
    ad = np.abs(fd)
    pin = (-np.sign(fd) * ts) > 0
    r = rng(seed, 404)
    # 刘海：正中最短，往两边略长；下沿一小绺一小绺的尖（长短不一）+ 低频起伏 + 三处分叉（露出一点额头）
    bang = BANG_G + 0.026 * np.clip(ad / 63.0, 0, 1) ** 2
    nt = 40
    fr = (u * nt) % 1.0
    tri = 1.0 - 2.0 * np.abs(fr - 0.5)
    lens = 0.35 + 0.65 * np.abs(np.sin(np.floor(u * nt) * 5.17 + seed * 0.37))
    bang = bang + 0.020 * tri ** 1.6 * lens + 0.006 * _noise1(u, sd(seed, 403), freq=9, octaves=1)
    for c, dep, wd in ((-31 + r.uniform(-4, 4), 0.042, 6.5), (6 + r.uniform(-3, 3), 0.030, 5.0),
                       (30 + r.uniform(-4, 4), 0.048, 7.0)):
        bang = bang - dep * np.clip(1.0 - np.abs(fd - c) / wd, 0, 1) ** 1.2
    # 发夹一侧：鬓发一绺 → 耳上 → 耳后一整片
    s_pin = np.interp(ad, [63.5, 66.0, 68.5, 71.5, 75.0, 77.5, 79.5, 98.0, 100.5, 104.0, 112.0, 130.0,
                           155.0, 180.0],
                      [0.10, 0.27, 0.330, 0.31, 0.24, 0.08, -0.012, -0.012, 0.26, 0.40, 0.46, 0.50, 0.52, 0.53])
    # 另一侧：bob 盖住耳朵
    s_oth = np.interp(ad, [63.5, 66.0, 69.0, 74.0, 85.0, 100.0, 115.0, 135.0, 160.0, 180.0],
                      [0.10, 0.30, 0.355, 0.375, 0.42, 0.45, 0.48, 0.505, 0.52, 0.53])
    side = np.where(pin, s_pin, s_oth)
    # 下沿的小发梢
    nt2 = 30
    fr2 = (u * nt2) % 1.0
    tri2 = 1.0 - 2.0 * np.abs(fr2 - 0.5)
    lens2 = 0.5 + 0.5 * np.abs(np.sin(np.floor(u * nt2) * 3.71 + seed * 0.53))
    tipk = np.where(pin, np.clip((ad - 101.0) / 6.0, 0, 1) + np.clip(1.0 - np.abs(ad - 70.0) / 6.0, 0, 1) * 0.5,
                    np.clip((ad - 67.0) / 4.0, 0, 1))
    side = side + 0.042 * tri2 ** 1.8 * lens2 * tipk
    return np.where(ad < 63.5, bang, side).astype(np.float32)


def _hair_shell_girl(seed, ts):
    """齐肩短发（短 bob）：齐刘海（下沿手绘参差 + 几缕分叉）、两侧鬓发贴着脸颊往下巴弯、发梢收尖；
    两侧头发别到耳后（露出耳朵），后面一整片到后颈。红豆发夹别在耳朵上方（PIN_SIDE 那一侧，模型 x 符号 ts）。
    每一列有自己的下沿（_girl_hair_low），比下沿低的环点收到下沿上（四边形退化，不画），所以下沿是逐列连续的。
    返回 (ry, Gh, phh)。约定 fch = phh - 90°（0 = 正前方）。"""
    ry, rw, rf, rb = _resample(_RY, [_RW, _RF, _RB], 38)
    rw = rw * 0.95
    rb = rb * 0.96
    Gh, phh = _rings(ry, rw, rf, rb, 120)
    fch = (phh - math.pi / 2 + math.pi) % (2 * math.pi) - math.pi
    ad = np.degrees(np.abs(fch))[None, :]
    phi_m = -np.degrees(fch)[None, :]                     # _surf 的方位（>0 朝 +x）
    zc = ((rf + rb) / 2)[:, None]
    # 耳朵上方：头发贴着头别到耳后（收紧一点）
    ek = (np.clip((ad - 72.0) / 6.0, 0, 1) * np.clip((108.0 - ad) / 6.0, 0, 1)) * \
        np.clip((ry[:, None] + 0.30) / 0.25, 0, 1) * ((-np.sign(np.degrees(fch)) * ts) > 0)[None, :]
    shrink = 1.0 - 0.055 * ek
    Gh[..., 0] *= shrink
    Gh[..., 2] = zc + (Gh[..., 2] - zc) * shrink
    # 每列下沿
    low = _girl_hair_low(seed, phh, ts)
    Y = np.minimum(Gh[..., 1], low[None, :])
    Gh[..., 1] = Y
    # 鬓发贴着脸颊：y 往下越贴近脸面（离脸 0.03），发梢往下巴方向弯一点；另一侧的 bob 只略微往里收
    pin = ((-np.sign(np.degrees(fch)) * ts) > 0)[None, :]
    colw = np.where(pin, 0.55 * np.clip((ad - 62.0) / 3.0, 0, 1) * np.clip((84.0 - ad) / 5.0, 0, 1),
                    0.50 * np.clip((ad - 62.0) / 4.0, 0, 1) * np.clip((110.0 - ad) / 20.0, 0, 1))
    hug = smooth01((Y + 0.07) / 0.24) * colw
    curl = 0.0 * Y
    ph_t = phi_m - np.sign(phi_m) * curl
    TY, TW, TF, TB = GIRL_FACE
    yy = np.clip(Y, TY[0], TY[-1])
    hw = np.interp(yy, TY, TW) + 0.032
    fr_ = np.interp(yy, TY, TF)
    bk_ = np.interp(yy, TY, TB)
    fzc, fhd = (fr_ + bk_) / 2, (fr_ - bk_) / 2 + 0.032
    a = np.radians(ph_t)
    tx, tz = hw * np.sin(a), fzc + fhd * np.cos(a)
    Gh[..., 0] = Gh[..., 0] * (1 - hug) + tx * hug
    Gh[..., 2] = Gh[..., 2] * (1 - hug) + tz * hug
    return ry, Gh, phh


def _hair_shell_boy(seed):
    """短发微乱：发壳下沿随方位变化（前额刘海 → 耳上 → 后颈），带一点起伏和参差的发梢。"""
    ry, rw, rf, rb = _resample(_SY, [_SW, _SF, _SB], 28)
    Gh, phh = _rings(ry, rw, rf, rb, 96)
    u = phh / (2 * math.pi)
    # 起伏：大一点的几团（蓬松、微乱）+ 细碎的
    bump = 1.0 + (0.045 * _noise1(u, sd(seed, 410), freq=6, octaves=1)[None, :] +
                  0.022 * _noise1(u, sd(seed, 412), freq=17, octaves=1)[None, :]) *         np.clip((ry[:, None] + 0.6) / 0.3, 0, 1)
    zc = ((rf + rb) / 2)[:, None]
    Gh[..., 0] *= bump
    Gh[..., 2] = zc + (Gh[..., 2] - zc) * bump
    fch = np.abs((phh - math.pi / 2 + math.pi) % (2 * math.pi) - math.pi)
    # 下沿：正前 -0.20（刘海，往一侧扫）→ 侧面 -0.03（耳上）→ 后面 0.20（后颈）
    low = np.interp(fch, [0.0, 0.7, 1.25, 1.75, 2.4, math.pi], [-0.19, -0.17, -0.06, -0.03, 0.24, 0.32])
    # 刘海往一侧扫：一侧长、一侧短
    sfd = (phh - math.pi / 2 + math.pi) % (2 * math.pi) - math.pi
    low = low + 0.035 * _noise1(u, sd(seed, 411), freq=11, octaves=1) + 0.045 * np.sin(sfd) * (fch < 1.3)
    # 发梢：一绺一绺往下的尖（前额和鬓角明显，后面弱），绺的长短不一
    nt = 26
    fr = (u * nt) % 1.0
    tri = 1.0 - 2.0 * np.abs(fr - 0.5)
    lens = 0.5 + 0.5 * np.abs(np.sin(np.floor(u * nt) * 7.31 + seed))
    front_w = np.clip(1.25 - fch / 1.6, 0.35, 1.0)
    low = low + 0.060 * (tri ** 1.8) * lens * front_w
    Y = Gh[..., 1]
    Gh[..., 1] = np.minimum(Y, low[None, :])
    return ry, Gh, phh


class _Raster:
    """画家算法的标签图：在屏幕坐标里（考虑 pen.view）按顺序填多边形，得到每个部件的可见遮罩和阴影图。"""

    def __init__(self, pen, bbox_scene, sc=2):
        self.s = float(pen.scale)
        self.o = pen.to_screen(np.zeros((1, 2), np.float32))[0].astype(np.float64)
        x0, y0, x1, y1 = bbox_scene
        X0 = int(math.floor(x0 * self.s + self.o[0])) - 4
        Y0 = int(math.floor(y0 * self.s + self.o[1])) - 4
        X1 = int(math.ceil(x1 * self.s + self.o[0])) + 4
        Y1 = int(math.ceil(y1 * self.s + self.o[1])) + 4
        X0, Y0 = max(X0, -64), max(Y0, -64)
        X1, Y1 = min(X1, W + 64), min(Y1, H + 64)
        X1, Y1 = max(X1, X0 + 8), max(Y1, Y0 + 8)
        self.X0, self.Y0, self.w, self.h = X0, Y0, X1 - X0, Y1 - Y0
        self.sc = sc
        self.lab = np.zeros((self.h * sc, self.w * sc), np.uint8)
        self.shd = np.zeros((self.h * sc, self.w * sc), np.uint8)
        self.masks = {}

    def q(self, P):
        P = np.asarray(P, np.float64)
        return np.round(((P * self.s + self.o) - (self.X0, self.Y0)) * self.sc * 4).astype(np.int32)

    def poly(self, P, label, shade=0):
        Q = self.q(P).reshape(-1, 2)
        cv2.fillPoly(self.lab, [Q], int(label), cv2.LINE_8, shift=2)
        cv2.fillPoly(self.shd, [Q], int(shade), cv2.LINE_8, shift=2)

    def quads(self, Q, labels, shades):
        """Q: (n,4,2) 场景坐标，已按从后到前排好。"""
        if len(Q) == 0:
            return
        I = self.q(Q)
        lab, shd = self.lab, self.shd
        for k in range(len(I)):
            cv2.fillConvexPoly(lab, I[k], int(labels[k]), cv2.LINE_8, shift=2)
            cv2.fillConvexPoly(shd, I[k], int(shades[k]), cv2.LINE_8, shift=2)

    def smooth_label(self, L, sigma, under):
        m = (self.lab == L).astype(np.float32)
        ms = cv2.GaussianBlur(m, (0, 0), sigma) > 0.5
        rem = (m > 0) & ~ms
        self.lab[rem] = under.lab[rem]
        self.shd[rem] = under.shd[rem]
        add = ms & (m == 0) & (self.lab != 0)
        self.lab[add] = L

    def finish(self, labels=(_HAIR, _FACE, _NECK, _EAR, _COLLAR)):
        for L in labels:
            m = (self.lab == L).astype(np.float32)
            self.masks[L] = cv2.resize(m, (self.w, self.h), interpolation=cv2.INTER_AREA)
        sh = self.shd.astype(np.float32) / 255.0
        self.shade = cv2.GaussianBlur(cv2.resize(sh, (self.w, self.h), interpolation=cv2.INTER_AREA), (0, 0),
                                      max(0.8, 1.0 * self.s))
        return self.masks

    def m(self, labels):
        if isinstance(labels, int):
            return self.masks[labels]
        out = np.zeros((self.h, self.w), np.float32)
        for L in labels:
            out += self.masks[L]
        return np.clip(out, 0, 1)

    def sample(self, M, P):
        """遮罩 M（屏幕 1x）在场景点 P 处的值（双线性近邻，越界=0）。"""
        P = np.asarray(P, np.float64).reshape(-1, 2)
        Q = P * self.s + self.o - (self.X0, self.Y0)
        xi = np.round(Q[:, 0]).astype(np.int64)
        yi = np.round(Q[:, 1]).astype(np.int64)
        ok = (xi >= 0) & (yi >= 0) & (xi < self.w) & (yi < self.h)
        out = np.zeros(len(P), np.float32)
        out[ok] = M[yi[ok], xi[ok]]
        return out

    def to_scene(self, Q):
        """屏幕 1x 遮罩坐标 → 场景坐标。"""
        Q = np.asarray(Q, np.float64)
        return ((Q + (self.X0, self.Y0)) - self.o) / self.s

    def emit(self, pen, kind, M, **kw):
        """把屏幕空间遮罩作为 mask 交给 pen（恒等取景）。"""
        if M is None or float(M.max()) < 0.02:
            return
        Mi = M
        x0, y0 = self.X0, self.Y0
        # 裁到画面
        cx0, cy0 = max(0, x0), max(0, y0)
        cx1, cy1 = min(W, x0 + self.w), min(H, y0 + self.h)
        if cx1 <= cx0 or cy1 <= cy0:
            return
        Mi = Mi[cy0 - y0:cy1 - y0, cx0 - x0:cx1 - x0]
        if float(Mi.max()) < 0.02:
            return
        with _screen(pen):
            getattr(pen, kind)(mask=(np.ascontiguousarray(Mi, np.float32), cx0, cy0), **kw)

    def outline(self, labels, allowed_out, min_len=12, smooth=3):
        """标签区域（labels 的并集）的轮廓，只保留“外侧邻居”在 allowed_out 里的段 → [场景坐标折线, ...]。"""
        reg = np.isin(self.lab, list(labels)).astype(np.uint8)
        cs, _ = cv2.findContours(reg, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        out = []
        hh, ww = self.lab.shape
        r = 3
        offs = [(r, 0), (-r, 0), (0, r), (0, -r), (2, 2), (-2, 2), (2, -2), (-2, -2)]
        allowed = np.array(sorted(set(allowed_out)), np.int32)
        for c in cs:
            c = c.reshape(-1, 2).astype(np.float32)
            if len(c) < min_len * self.sc:
                continue
            # 环向平滑
            k = smooth * self.sc
            if len(c) > 2 * k + 2:
                ker = np.ones(2 * k + 1, np.float32) / (2 * k + 1)
                cx = np.convolve(np.concatenate([c[-k:, 0], c[:, 0], c[:k, 0]]), ker, 'valid')
                cy = np.convolve(np.concatenate([c[-k:, 1], c[:, 1], c[:k, 1]]), ker, 'valid')
                cc = np.stack([cx, cy], 1)
            else:
                cc = c
            ci = c.astype(np.int64)
            nb = []
            for dx, dy in offs:
                xs = np.clip(ci[:, 0] + dx, 0, ww - 1)
                ys = np.clip(ci[:, 1] + dy, 0, hh - 1)
                nb.append(self.lab[ys, xs])
            nb = np.stack(nb, 1)
            outside = ~np.isin(nb, list(labels))
            okp = np.zeros(len(c), bool)
            for a in allowed:
                okp |= ((nb == a) & outside).any(1)
            # 去掉孤立的小段：形态学“闭运算”式填补 2 个点以内的缺口
            if okp.any() and not okp.all():
                okp = np.convolve(np.concatenate([okp[-3:], okp, okp[:3]]).astype(np.float32),
                                  np.ones(7) / 7, 'valid') > 0.42
            if okp.all():
                # 闭合轮廓：从稳定的位置（最上方的点）起笔
                j0 = int(np.argmin(cc[:, 1]))
                cc2 = np.roll(cc, -j0, 0)
                pts = cc2[::max(1, int(2.5 * self.sc))]
                out.append((self.to_scene(pts / self.sc), True))
                continue
            # 旋转到一个 False 处起，切段
            if not okp.any():
                continue
            j0 = int(np.argmin(okp))
            okr = np.roll(okp, -j0)
            ccr = np.roll(cc, -j0, 0)
            for a, b, _, _ in _runs(ccr, okr, min_pts=int(min_len * self.sc)):
                seg = ccr[a:b:max(1, int(2.5 * self.sc))]
                if len(seg) >= 3:
                    out.append((self.to_scene(seg / self.sc), False))
        return out


# =========================================================================== 眼、眉、嘴（她和他共用，参数不同）
def _phc(R, phi):
    """转头时远侧的五官往脸中线收一点（画家的习惯：远侧眼睛不贴着脸的外轮廓）。"""
    yaw = float(R.proj.yaw)
    if phi * yaw <= 0:
        return phi
    k = 1.0 - 0.24 * float(np.clip((abs(yaw) - 15.0) / 45.0, 0.0, 1.0))
    return phi * k


def _clip_poly(P, C):
    """多边形 P ∩ C → 多边形列表（shapely；没有就原样返回 P）。"""
    if _SPoly is None:
        return [P]
    try:
        g = _make_valid(_SPoly(P)).intersection(_make_valid(_SPoly(C)))
    except Exception:
        return []
    out = []
    for q in getattr(g, 'geoms', [g]):
        if q.geom_type == 'Polygon' and q.area > 0.3:
            out.append(np.asarray(q.exterior.coords, np.float32)[:-1])
    return out


def _eye(ink, R, side, e, sty):
    """一只眼。side=-1 模型 -x 一侧，+1 模型 +x 一侧。sty：尺寸/睫毛等风格参数。
    黑眼珠固定在眼眶里（不随睁眼程度上下跑），上眼皮放下来时盖住黑眼珠的上半——半垂的眼皮、柔和的眼神；
    眼白上沿有一道眼皮的投影；高光只画在看得见的那部分黑眼珠里。"""
    proj, S, tab = R.proj, R.S, R.face_tab
    inner3 = _surf(tab, sty['y_in'], _phc(R, sty['ph_in'] * side), dz=0.004)
    outer3 = _surf(tab, sty['y_out'], _phc(R, sty['ph_out'] * side), dz=0.0)
    (pi, po), z = proj(np.float32([inner3, outer3]), with_z=True)
    zm = float(z.mean())
    if zm < 0.02 or R.back:
        return None
    vis = float(np.clip(zm / 0.22, 0.30, 1.0))
    L = float(np.hypot(*(po - pi))) + 1e-6
    L0 = float(np.hypot(*(outer3[:2] - inner3[:2]))) * S
    fs = float(np.clip(L / (L0 + 1e-6), 0.25, 1.15))
    e1 = (po - pi) / L
    upv = R.head_up
    up = _perp(e1)
    if float(np.dot(up, upv)) < 0:
        up = -up
    op = float(np.clip(e['open'], 0.0, 1.2))
    happy = float(e.get('happy', 0.0))
    gx, gy = float(e.get('gx', 0.0)), float(e.get('gy', 0.0))
    seed = R.seed + 810 + 7 * (side > 0)
    keep = R.keep_face
    lw = sty['lid_w'] * S * (0.75 + 0.25 * vis)
    mid = (pi + po) / 2
    info = dict(inner=pi, outer=po, c=mid, up=up)
    if op < 0.18:
        # 闭眼：∩（笑眼）或 ‿（安静地闭着）
        if happy > 0.5:
            arc = [pi, pi + e1 * 0.5 * L + up * sty['hu'] * S * 0.50, po]
        else:
            arc = [pi, pi + e1 * 0.52 * L - up * sty['hu'] * S * 0.30, po]
        ink.line(spline(np.float32(arc), 3.0), lw * 1.25, tone=0.88 * vis, seed=seed, role='feature', color='eye',
                 taper=(0.35, 0.25), keep=keep, clip=False)
        if sty['lashes']:
            nl = 3 if happy <= 0.5 else 2
            curve = spline(np.float32(arc), 2.0)
            for k in range(nl):
                tt = 0.62 + 0.15 * k
                p0 = curve[int(tt * (len(curve) - 1))]
                dirv = (-up * 0.030 + e1 * 0.010) if happy <= 0.5 else (up * 0.020 + e1 * 0.016)
                ink.line([p0, p0 + dirv * S], 0.010 * S, tone=0.55 * vis, seed=seed + 5 + k, role='feature',
                         color='eye', taper=(0.1, 0.8), keep=keep, clip=False)
        info.update(lower=np.float32([pi, mid - up * 0.02 * S, po]), closed=True)
        return info
    hu_full = sty['hu'] * S
    hu = hu_full * min(op, 1.2)
    hl = sty['hl'] * S * (0.55 + 0.45 * min(op, 1.0)) * (1.0 - 0.35 * happy)
    lift_low = sty['hl'] * S * 0.60 * happy          # 笑眼：下眼睑往上推
    upper = np.float32([pi, pi + e1 * 0.22 * L + up * 0.80 * hu, pi + e1 * 0.52 * L + up * 1.0 * hu,
                        pi + e1 * 0.82 * L + up * 0.70 * hu, po])
    lower = np.float32([pi, pi + e1 * 0.35 * L - up * (hl - lift_low * 0.5), pi + e1 * 0.70 * L - up * (0.9 * hl - lift_low),
                        po])
    U = spline(upper, 1.5)
    Lo = spline(lower, 1.5)
    opening = np.vstack([U, Lo[::-1][1:-1]])
    # 眼白：先挡掉皮肤再上一点白（蓝纸上也是白的）
    ink.pen.cover(opening, seed=seed + 1, amount=0.85, feather=0.6)
    ink.pen.fill(opening, EYE_WHITE, seed=seed + 2)
    # 上眼皮投在眼白上的影
    band = np.vstack([U, (U - up * 0.040 * S)[::-1]])
    sh = _clip_poly(band, opening)
    if sh:
        ink.pen.shade(sh, amount=0.30, seed=seed + 12, color='skin_sh', soft=1.5)
    # 黑眼珠：位置固定在眼眶里（按完全睁开的眼算），被上下眼睑裁切
    r = sty['iris'] * S
    cu = sty.get('iris_up', 0.40) * hu_full - 0.032 * S * gy - lift_low * 0.25
    c = mid + e1 * (0.05 * L + 0.17 * L * gx) + up * cu
    iris = ell(c[0], c[1], r * max(fs, 0.55), r, n=32, rot=math.degrees(math.atan2(e1[1], e1[0])))
    parts = _clip_poly(iris, opening)
    if parts:
        ink.pen.fill(parts, sty.get('iris_c', 'eye'), seed=seed + 3, tone=0.90)
        # 瞳孔 + 黑眼珠上半被眼皮压暗（A/B 里看得出层次；水墨里本来就是浓墨）
        pup = _clip_poly(ell(c[0], c[1], 0.48 * r * max(fs, 0.55), 0.50 * r, n=20,
                             rot=math.degrees(math.atan2(e1[1], e1[0]))), opening)
        if pup:
            ink.pen.fill(pup, 'eye', seed=seed + 13, tone=0.95)
        # 黑眼珠下半一团透亮（湿润、温柔）
        gc = c - up * 0.42 * r
        glow = ell(gc[0], gc[1], 0.52 * r * max(fs, 0.55), 0.30 * r, n=16, rot=math.degrees(math.atan2(e1[1], e1[0])))
        cr = [q for p_ in parts for q in _clip_poly(glow, p_)]
        if cr:
            ink.pen.lift(cr, amt=0.13 + 0.10 * float(e.get('wet', 0.0)), seed=seed + 14, soft=1.6)
        # 高光（留白）：上方一大颗（放在看得见的黑眼珠的上部），下方一小颗
        top_vis = float(np.dot(np.float32(U[len(U) // 2]) - mid, up))
        hy = min(cu + 0.40 * r, top_vis - 0.30 * r)
        hc = mid + e1 * (0.05 * L + 0.17 * L * gx) - e1 * 0.30 * r * fs * R.light + up * hy
        hl1 = _clip_poly(ell(hc[0], hc[1], 0.23 * r, 0.20 * r, n=14), opening)
        if hl1 and op > 0.25:
            ink.pen.lift(hl1, amt=0.95, seed=seed + 4, soft=0.5)
        hc2 = c + e1 * 0.36 * r * fs * R.light - up * 0.42 * r
        hl2 = _clip_poly(ell(hc2[0], hc2[1], 0.085 * r, 0.085 * r, n=8), opening)
        if hl2:
            ink.pen.lift(hl2, amt=0.65 + 0.3 * float(e.get('wet', 0.0)), seed=seed + 5, soft=0.4)
    # 上眼皮（睫毛线）：一笔，外半段略重
    ink.line(U[::3] if len(U) > 9 else U, lw, tone=0.86 * vis, seed=seed + 6, role='feature', color='eye',
             taper=(0.45, 0.25), keep=keep, clip=False, b_width=0.8)
    seg = U[int(len(U) * 0.45):]
    if len(seg) > 4:
        ink.line(seg[::3], lw * 0.65, tone=0.80 * vis, seed=seed + 7, role='feature', color='eye',
                 taper=(0.6, 0.3), keep=keep, clip=False, b_width=0.7)
    if sty['lashes']:
        for k, tt in enumerate((0.74, 0.88)):
            p0 = U[int(tt * (len(U) - 1))]
            ink.line([p0, p0 + up * 0.012 * S + e1 * 0.009 * S], 0.008 * S * vis, tone=0.40 * vis,
                     seed=seed + 8 + k, role='feature', color='eye', taper=(0.1, 0.8), keep=keep, clip=False)
        # 双眼皮：一道很淡的细线（眼皮放松时离睫毛线近一点）
        crease = U[int(len(U) * 0.28):int(len(U) * 0.92)] + up * (0.018 + 0.010 * min(op, 1.0)) * S
        if len(crease) > 3:
            ink.line(crease[::3], 0.008 * S, tone=0.20 * vis, seed=seed + 10, role='feature', color='eye',
                     taper=(0.4, 0.4), keep=keep, clip=False)
    # 下眼睑：外半段一笔淡线
    lo_seg = Lo[int(len(Lo) * 0.40):]
    ink.line(lo_seg[::3] if len(lo_seg) > 9 else lo_seg, 0.010 * S, tone=0.36 * vis, seed=seed + 11,
             role='feature', color='eye', taper=(0.5, 0.3), keep=keep, clip=False)
    info.update(c=c, r=r, lower=Lo)
    return info


def _brow(ink, R, side, e, sty):
    tab = R.face_tab
    br = float(e.get('brow', 0.0))
    by = float(e.get('brow_y', 0.0))
    bo = float(e.get('brow_out', 0.0))
    y0 = sty['brow_y']
    ar = sty.get('brow_arch', (0.022, 0.000, 0.012))
    P3 = np.stack([_surf(tab, y0 + ar[0] - 0.032 * br - 0.03 * by, _phc(R, sty['brow_ph'][0] * side), dz=0.012),
                   _surf(tab, y0 + ar[1] - 0.008 * br - 0.035 * by + 0.004 * bo, _phc(R, sty['brow_ph'][1] * side),
                         dz=0.012),
                   _surf(tab, y0 + ar[2] + 0.020 * br - 0.03 * by + 0.024 * bo, _phc(R, sty['brow_ph'][2] * side),
                         dz=0.006)])
    p, z = R.proj(P3, with_z=True)
    if float(z.mean()) < 0.02 or R.back:
        return
    vis = float(np.clip(z.mean() / 0.2, 0.4, 1.0))
    ink.line(p, sty['brow_w'] * R.S, tone=sty['brow_t'] * vis, seed=R.seed + 800 + (side > 0), role='feature',
             color=sty['brow_c'], taper=(0.25, 0.6), keep=R.keep_face, clip=False, head=0.2)


def _mouth(ink, R, e, sty):
    proj, S, tab = R.proj, R.S, R.face_tab
    if R.back:
        return
    sm = float(e.get('smile', 0.0))
    mo = float(e.get('mouth_open', 0.0))
    pk = float(e.get('pucker', 0.0))
    y0 = sty['mouth_y']
    hw = sty['mouth_ph'] * (1.0 - 0.45 * pk) * (1.0 + 0.10 * max(sm, 0))
    ctr3 = _surf(tab, y0, 0.0)
    _, zc = proj(ctr3[None], with_z=True)
    if float(zc[0]) < 0.0:
        return
    L3 = _surf(tab, y0 - 0.026 * sm, -hw)
    M3 = _surf(tab, y0 + 0.006 + 0.010 * sm, 0.0, dz=0.010)
    R3 = _surf(tab, y0 - 0.030 * sm, hw)
    mp, mz = proj(np.stack([L3, M3, R3]), with_z=True)
    seed = R.seed + 840
    col = sty['lip_c']
    lips = 'lips'
    if ink.pen.style == 'B' and sty.get('lip_b'):
        # 油画棒的 'lips' 太艳（像口红）：唇线、下唇都用淡的肤色暗部
        col = lips = sty['lip_b']
    bcol = {}
    keep = R.keep_face
    if pk > 0.3:
        # 嘟嘴：一颗小小的圆唇
        c = proj(_surf(tab, y0 + 0.012, 0.0, dz=0.03)[None])[0]
        rx, ry = 0.040 * S * (0.6 + 0.4 * pk), 0.030 * S
        lip = ell(c[0], c[1], rx, ry, n=16)
        ink.pen.fill(lip, lips, seed=seed + 1)
        ink.line(ell(c[0], c[1] - 0.004 * S, rx * 0.8, ry * 0.25, 190, 350, 8), 0.013 * S, tone=0.6, seed=seed + 2,
                 role='feature', color=lips, taper=(0.3, 0.3), clip=False)
        ink.line(ell(c[0], c[1], rx, ry, 20, 160, 8), 0.012 * S, tone=0.45, seed=seed + 3, role='feature',
                 color='lips', taper=(0.3, 0.3), clip=False)
        return
    if mo > 0.03:
        dep = (0.050 + 0.070 * mo) * (1.0 + 0.3 * max(sm, 0))
        low3 = np.stack([_surf(tab, y0 - 0.02 * sm + 0.01, -hw * 0.85), _surf(tab, y0 + dep, 0.0, dz=0.01),
                         _surf(tab, y0 - 0.02 * sm + 0.01, hw * 0.85)])
        lowp = proj(low3)
        U = spline(mp, 1.5)
        Lw = spline(np.vstack([mp[:1], lowp, mp[-1:]]), 1.5)
        inside = np.vstack([U, Lw[::-1][1:-1]])
        ink.pen.cover(inside, seed=seed + 4, amount=0.9, feather=0.6)
        ink.pen.fill(inside, MOUTH_IN if ink.pen.style != 'B' else '#8E5A58', seed=seed + 5, tone=0.42)
        if sm > 0.5:
            # 上排牙一点留白
            tooth = np.vstack([U[len(U) // 5:-len(U) // 5], (U[len(U) // 5:-len(U) // 5] + (0, 0.018 * S))[::-1]])
            ink.pen.fill(tooth, EYE_WHITE, seed=seed + 6)
        ink.line(Lw[::3], 0.014 * S, tone=0.55, seed=seed + 7, role='feature', color=col, taper=(0.3, 0.3),
                 keep=keep, clip=False)
    ink.line(mp, sty['mouth_w'] * S, tone=0.50, seed=seed, role='feature', color=col, taper=(0.4, 0.45),
             keep=keep, clip=False, head=0.1, **bcol)
    if sm > 0.35 and mo < 0.1 and sty.get('dimple', True):
        # 嘴角一点小顿笔
        k = min(1.0, (sm - 0.35) / 0.4)
        for i, (p_, s_) in enumerate(((mp[0], -1), (mp[-1], 1))):
            if mz[0 if s_ < 0 else 2] < 0.05:
                continue
            d_ = _unit(p_ - mp[1])
            ink.line([p_ - d_ * 0.004 * S, p_ + d_ * 0.012 * S - R.head_up * 0.012 * S], 0.010 * S, tone=0.4 * k,
                     seed=seed + 20 + i, role='feature', color=col, taper=(0.3, 0.6), keep=keep, clip=False,
                     **bcol)
    if mo < 0.1:
        # 下唇：一小笔很淡的唇色
        lp = proj(np.stack([_surf(tab, y0 + 0.045, -0.35 * hw), _surf(tab, y0 + 0.048, 0.35 * hw)]))
        ink.line(lp, 0.014 * S, tone=0.14, seed=seed + 30, role='feature', color=lips, taper=(0.5, 0.5),
                 keep=keep, clip=False, **bcol)
    if sm < -0.2 and mo < 0.1:
        k = min(1.0, (-sm - 0.2) / 0.3)
        d_ = _unit(mp[0] - mp[1])
        ink.line([mp[0], mp[0] + d_ * 0.01 * S + R.head_up * -0.014 * S], 0.010 * S, tone=0.35 * k,
                 seed=seed + 40, role='feature', color=col, taper=(0.2, 0.6), keep=keep, clip=False)


def _nose(ink, R, sty):
    if R.back:
        return
    tab = R.face_tab
    y_t = sty['nose_y']
    P3 = np.stack([_surf(tab, y_t - 0.06, 3, dz=0.02), _surf(tab, y_t - 0.005, 3, dz=0.055),
                   _surf(tab, y_t + 0.012, -7, dz=0.03)])
    p, z = R.proj(P3, with_z=True)
    if float(z.mean()) < 0.05:
        return
    ink.line(p, sty['nose_w'] * R.S, tone=sty['nose_t'], seed=R.seed + 830, role='feature', color='skin_sh',
             taper=(0.5, 0.3), keep=R.keep_face, clip=False)


def _blush(ink, R, e, sty):
    amt = float(e.get('blush', 0.0))
    if amt < 0.03 or R.back:
        return
    S = R.S
    for side in (-1, 1):
        c3 = _surf(R.face_tab, sty['blush_y'], sty['blush_ph'] * side, dz=0.01)
        c, z = R.proj(c3[None], with_z=True)
        if float(z[0]) < 0.08:
            continue
        # 沿脸面的两个切向量估计投影后的椭圆
        a3 = _surf(R.face_tab, sty['blush_y'], (sty['blush_ph'] + 9) * side, dz=0.01)
        b3 = _surf(R.face_tab, sty['blush_y'] + 0.045, sty['blush_ph'] * side, dz=0.01)
        pa, pb = R.proj(np.stack([a3, b3]))
        c = c[0]
        ux, uy = pa - c, pb - c
        th = np.radians(np.linspace(0, 360, 20, endpoint=False))
        poly = c + np.outer(np.cos(th), ux) + np.outer(np.sin(th), uy)
        rr = float(max(np.hypot(*ux), np.hypot(*uy)))
        # 柔和的一团：椭圆遮罩高斯模糊成软边（不是硬边的色块），再按到脸上
        ell_m = _poly_mask_screen(R.raster, c + (poly - c) * 0.75)
        sig = max(1.0, 0.42 * rr * R.raster.s)
        Mb = R.raster.m(_FACE) * np.clip(cv2.GaussianBlur(ell_m, (0, 0), sig) * 1.25, 0, 1) * (0.55 + 0.45 * amt)
        if ink.pen.style == 'B':
            # 油画棒：一层很淡的玫瑰色轻轻擦上去（shade 的 color 模式），不是一块实涂
            R.raster.emit(ink.pen, 'shade', Mb, amount=0.20 * amt + 0.06, color='blush', b_mode='color',
                          seed=R.seed + 870 + (side > 0), angle=35, b_size=0.6)
        else:
            R.raster.emit(ink.pen, 'fill', Mb, color='blush', seed=R.seed + 870 + (side > 0),
                          rgrad=tuple(np.concatenate([R.raster.to_screen_pt(c), [0.0, rr * R.raster.s * 1.25,
                                                                                 0.80 * amt, 0.0]]).tolist()),
                          soft=4.0, a_soft=1.0)


def _poly_mask_screen(raster, poly):
    m = np.zeros((raster.h, raster.w), np.uint8)
    P = np.asarray(poly, np.float64) * raster.s + raster.o - (raster.X0, raster.Y0)
    cv2.fillPoly(m, [np.round(P * 16).astype(np.int32)], 255, cv2.LINE_AA, shift=4)
    return m.astype(np.float32) / 255.0


def _to_screen_pt(self, p):
    return np.asarray(p, np.float64) * self.s + self.o


_Raster.to_screen_pt = _to_screen_pt


def _tear(ink, R, e, sty, eyes):
    k = float(e.get('tear', 0.0))
    if k < 0.04 or R.back:
        return
    S = R.S
    # 只画近侧（z 大的那只）眼下的一道泪
    best = None
    for side in (-1, 1):
        p3 = _surf(R.face_tab, sty['y_in'] + 0.045, (sty['ph_in'] + 14) * side)
        _, z = R.proj(p3[None], with_z=True)
        if best is None or z[0] > best[1]:
            best = (side, float(z[0]))
    side = best[0]
    ph = (sty['ph_in'] + 15) * side
    ys = np.linspace(sty['y_in'] + 0.05, sty['y_in'] + 0.05 + 0.24 * k, 6)
    p, z = R.proj(_surf(R.face_tab, ys, ph + 4 * side * np.linspace(0, 1, 6), dz=0.006), with_z=True)
    if float(z.mean()) < 0.03:
        return
    ink.line(p, 0.016 * S, tone=0.30, seed=R.seed + 850, role='feature', color='tear', taper=(0.3, 0.1),
             keep=R.keep_face, clip=False)
    end = p[-1]
    ink.pen.fill(ell(end[0], end[1] + 0.012 * S, 0.020 * S, 0.028 * S, n=14), 'tear', seed=R.seed + 851)
    ink.line(ell(end[0], end[1] + 0.012 * S, 0.020 * S, 0.028 * S, 10, 170, 8), 0.008 * S, tone=0.35,
             seed=R.seed + 852, role='feature', color='tear', taper=(0.2, 0.2), clip=False)
    ink.pen.lift(ell(end[0] - 0.006 * S, end[1] + 0.004 * S, 0.006 * S, 0.008 * S, n=8), amt=0.8,
                 seed=R.seed + 853, soft=0.4)
    # 眼眶泛红：眼下一抹淡淡的腮红色
    for ei in eyes:
        if ei is None or 'lower' not in ei:
            continue
        Lo = ei['lower']
        band = np.vstack([Lo, (Lo - ei['up'] * 0.035 * S)[::-1]])
        ink.pen.fill(band, 'blush', seed=R.seed + 856, soft=3.0)


GIRL_FEAT = dict(y_in=0.100, ph_in=13, y_out=0.092, ph_out=42, hu=0.100, hl=0.050, iris=0.068, lid_w=0.019,
                 iris_up=0.40, iris_c='#3E2B2A',
                 lashes=True, brow_y=-0.026, brow_ph=(12, 27, 41), brow_w=0.020, brow_t=0.50, brow_c='hair',
                 brow_arch=(0.006, -0.008, 0.016),
                 mouth_y=0.318, mouth_ph=12, mouth_w=0.016, lip_c='lips', lip_b='skin_sh', nose_y=0.222,
                 nose_w=0.014, nose_t=0.40, blush_y=0.205, blush_ph=40)
BOY_FEAT = dict(y_in=0.050, ph_in=12, y_out=0.044, ph_out=40, hu=0.066, hl=0.028, iris=0.044, lid_w=0.024,
                lashes=False, brow_y=-0.095, brow_ph=(9, 25, 42), brow_w=0.028, brow_t=0.78, brow_c='boy_hair',
                mouth_y=0.300, mouth_ph=15, mouth_w=0.020, lip_c='lips', lip_b='skin_sh', nose_y=0.195, nose_w=0.019,
                nose_t=0.55,
                blush_y=0.18, blush_ph=42, dimple=False)


# =========================================================================== 头（她、他共用的装配）
class _HeadRig:
    pass


def _build_head(pen, R, who):
    """建 2.5D 头：画家算法得到 头发/脸/脖子/耳/高领 的屏幕遮罩，存在 R.raster；返回绘制所需的中间量。"""
    S, f = R.S, R.f
    proj = R.proj
    girl_ = who == 'girl'
    tab = R.face_tab
    # 发壳
    if girl_:
        ry, Gh, phh = _hair_shell_girl(R.seed, R.ts)
    else:
        ry, Gh, phh = _hair_shell_boy(R.seed)
    Ph, Zh = proj(Gh, with_z=True)
    fch = (phh - math.pi / 2 + math.pi) % (2 * math.pi) - math.pi
    # 从背后看（头的正前方朝里）：后面的头发在脖子前面，不再“垫在脖子后面”
    back_view = float(proj.R[2, 2]) < -0.15
    R.back_view = back_view
    keep = np.ones(Gh.shape[:2], bool)
    if girl_ and not back_view:
        # 比脖子更靠后、又垂到耳朵以下的头发：先画，被脖子/领子挡住（远侧和后面的发尾）
        _, zn = proj(np.float32([[0.0, 0.40, -0.06]]), with_z=True)
        back_k = (Zh < float(zn[0]) - 0.03) & (Gh[..., 1] > 0.15)
    else:
        back_k = np.zeros(Gh.shape[:2], bool)
    # 脸
    hy, hw, hf, hb = _resample(tab[0], list(tab[1:]), 22)
    G, ph = _rings(hy, hw, hf, hb, 40)
    Pg, Zg = proj(G, with_z=True)
    # 耳朵（两侧；她的头发别在耳后）
    ears = []
    for es in (-1, 1):
        ecy = 0.105 if girl_ else 0.075
        hwv = float(np.interp(ecy, tab[0], tab[1]))
        th = np.radians(np.linspace(-100, 100, 9))
        cy, cz = ecy, -0.035
        rim = np.stack([np.full_like(th, es * (hwv + 0.035)), cy + 0.088 * np.sin(th) * -1.0 + 0.0,
                        cz - 0.055 * np.cos(th) + 0.02], 1)
        rim[:, 1] = cy - 0.088 * np.cos(th)
        rim[:, 2] = cz - 0.050 * np.sin(th) * 0.9
        base = np.stack([np.full_like(th, es * (hwv - 0.01)), cy - 0.07 * np.cos(th), cz - 0.03 * np.sin(th)], 1)
        ears.append((es, rim.astype(np.float32), base.astype(np.float32)))
    # 脖子（两圈之间的凸包：头底一圈 + 颈根一圈）
    a = np.radians(np.linspace(0, 360, 16, endpoint=False))
    top3 = np.stack([0.13 * np.cos(a), np.full_like(a, 0.30), -0.06 + 0.12 * np.sin(a)], 1).astype(np.float32)
    top2 = proj(top3)
    nb = R.TB(np.stack([0.17 * np.cos(a), -0.10 + 0.045 * np.sin(a)], 1))
    neck = cv2.convexHull(np.vstack([top2, nb]).astype(np.float32)).reshape(-1, 2)
    # 领子（她：高领翻折一圈；他：衬衫领 + 毛衣 V 领在身体部分画，这里只画领口一圈衬衫领座）
    if R.back:
        # 背影：领子是左右对称的一圈（高领 / 衬衫领座），上沿比正面低一点，露出一点后颈
        hgt = -0.17 if girl_ else -0.13
        wdt = 0.25 if girl_ else 0.22
        collar = spline(R.TB([(-wdt, hgt + 0.02), (0.0, hgt), (wdt, hgt + 0.02), (wdt + 0.03, 0.0), (0.0, 0.04),
                              (-wdt - 0.03, 0.0)]), 2.0, closed=True)
    elif girl_:
        collar = spline(R.TB([(-0.25, -0.19), (-0.02, -0.25), (0.20, -0.22), (0.24, -0.03), (0.0, 0.03),
                              (-0.28, -0.01)]), 2.0, closed=True)
    else:
        collar = spline(R.TB([(-0.20, -0.13), (0.0, -0.17), (0.20, -0.14), (0.22, -0.04), (0.0, 0.0),
                              (-0.22, -0.03)]), 2.0, closed=True)
    # 栅格范围
    allp = np.vstack([Ph.reshape(-1, 2), Pg.reshape(-1, 2), neck, collar] + [proj(r) for _, r, _ in ears])
    pad = 0.08 * S
    bbox = (float(allp[:, 0].min() - pad), float(allp[:, 1].min() - pad),
            float(allp[:, 0].max() + pad), float(allp[:, 1].max() + pad))
    ras = _Raster(pen, bbox)
    R.raster = ras
    # ---- 光照：旋转后的空间里算每个四边形的法线
    Lx = 0.50 * R.light
    Ldir = np.float32([Lx * f, -0.55, 0.68])
    Ldir /= np.linalg.norm(Ldir)
    R.Ldir = Ldir

    def shade_of(Q3):
        n = _normals(Q3)
        ctr = Q3.mean(axis=-2)
        sgn = np.sign((n * (ctr - R.proj.rot(np.float32([0, 0.0, -0.02]))[None])).sum(-1, keepdims=True) + 1e-6)
        n = n * sgn
        ndl = (n * Ldir).sum(-1)
        return np.clip((0.18 - ndl) / 0.42, 0, 1)

    # 头发四边形
    QH3 = _quads(proj.rot(Gh))
    QH2 = _quads(Ph)
    ZH = _quads(Zh[..., None])[..., 0].mean(-1)
    kq = _quads(keep[..., None].astype(np.float32))[..., 0].min(-1) > 0.5
    bq = _quads(back_k[..., None].astype(np.float32))[..., 0].min(-1) > 0.5
    shH = shade_of(QH3)
    # 脸四边形
    QG3 = _quads(proj.rot(G))
    QG2 = _quads(Pg)
    ZG = _quads(Zg[..., None])[..., 0].mean(-1)
    shG = shade_of(QG3)
    # 耳四边形（扇形）
    QE2, ZE, shE = [], [], []
    for es, rim, base in ears:
        r2, rz = proj(rim, with_z=True)
        b2, bz = proj(base, with_z=True)
        for k in range(len(rim) - 1):
            QE2.append(np.stack([b2[k], r2[k], r2[k + 1], b2[k + 1]]))
            ZE.append(float((rz[k] + rz[k + 1] + bz[k] + bz[k + 1]) / 4) + 0.01)
            shE.append(0.35)
    # 1. 后垂发（脖子后面）
    sel = kq & bq
    if sel.any():
        order = np.argsort(ZH[sel])
        ras.quads(QH2[sel][order], np.full(int(sel.sum()), _HAIR), (shH[sel][order] * 255).astype(np.uint8))
    # 2. 脖子、领子
    ras.poly(neck, _NECK, 150)
    ras.poly(collar, _COLLAR, 0)
    # 3. 脸 + 耳 + 其余头发，按深度
    selh = kq & ~bq
    Qs = [QG2.reshape(-1, 4, 2), QH2[selh]]
    Zs = [ZG.reshape(-1), ZH[selh]]
    Ls = [np.full(QG2.shape[0] * QG2.shape[1], _FACE), np.full(int(selh.sum()), _HAIR)]
    Ss = [shG.reshape(-1), shH[selh]]
    if QE2:
        Qs.append(np.float32(QE2))
        Zs.append(np.float32(ZE))
        Ls.append(np.full(len(QE2), _EAR))
        Ss.append(np.float32(shE))
    Qa, Za, La, Sa = (np.concatenate(x) for x in (Qs, Zs, Ls, Ss))
    order = np.argsort(Za, kind='stable')
    ras.quads(Qa[order], La[order], (Sa[order] * 255).astype(np.uint8))
    # 发壳是一圈圈截面拼的，刘海/鬓角的边会有台阶：再画一张“没有前面头发”的标签图，
    # 把头发区域模糊后取阈值（圆顺的发际线），被削掉的地方露出下面那一层。
    under = _Raster(pen, bbox)
    if sel.any():
        o2 = np.argsort(ZH[sel])
        under.quads(QH2[sel][o2], np.full(int(sel.sum()), _HAIR), (shH[sel][o2] * 255).astype(np.uint8))
    under.poly(neck, _NECK, 150)
    under.poly(collar, _COLLAR, 0)
    nf = La != _HAIR
    o3 = np.argsort(Za[nf], kind='stable')
    under.quads(Qa[nf][o3], La[nf][o3], (Sa[nf][o3] * 255).astype(np.uint8))
    ras.smooth_label(_HAIR, max(1.2, (0.006 if girl_ else 0.008) * S * ras.s * ras.sc), under)
    ras.finish()
    # 不被头发挡住的点（五官/脸上的线用）
    hm = ras.masks[_HAIR]
    fm = np.clip(ras.masks[_FACE] + ras.masks[_EAR], 0, 1)

    def keep_face(P):
        return (ras.sample(hm, P) < 0.5) & (ras.sample(cv2.dilate(fm, np.ones((3, 3), np.uint8)), P) > 0.3)

    R.keep_face = keep_face
    hd = dict(ry=ry, Gh=Gh, Ph=Ph, Zh=Zh, phh=phh, fch=fch, keep=keep, Pg=Pg, Zg=Zg, neck=neck, collar=collar,
              ears=ears)
    return hd


def _dedupe(P, eps):
    """去掉挨得太近的连续点（收到发梢下沿上的重复点）。"""
    P = np.asarray(P, np.float32).reshape(-1, 2)
    if len(P) < 2:
        return P
    out = [P[0]]
    for q in P[1:]:
        if float(np.hypot(*(q - out[-1]))) > eps:
            out.append(q)
    return np.float32(out)


def _shift(M, v):
    """遮罩平移 v=(dx,dy) 像素（屏幕）。"""
    h, w = M.shape
    return cv2.warpAffine(M, np.float32([[1, 0, float(v[0])], [0, 1, float(v[1])]]), (w, h),
                          flags=cv2.INTER_LINEAR, borderValue=0)


def _cheek_hollow(R, ras):
    """颧骨下那一小片很轻的影：背光一侧脸颊的一块面片（脸面上的 y/方位范围）投影 → 软遮罩。"""
    best = None
    for sd_ in (-1, 1):
        n3 = _unit(np.float32([0.80 * sd_, 0.25, 0.55]))
        nz = float((R.proj.R @ n3)[2])
        if nz < 0.05:
            continue
        ndl = float((R.proj.R @ n3) @ R.Ldir)
        if best is None or ndl < best[1]:
            best = (sd_, ndl)
    if best is None or best[1] > 0.55:
        return None
    sd_ = best[0]
    ys = np.linspace(0.19, 0.37, 7)
    ph0, ph1 = 38.0, 82.0
    edge = [(_surf(R.face_tab, y, ph0 * sd_)) for y in ys] + [(_surf(R.face_tab, y, ph1 * sd_)) for y in ys[::-1]]
    poly = R.proj(np.float32(edge))
    m = _poly_mask_screen(ras, poly)
    k = float(np.clip((0.55 - best[1]) / 0.4, 0.3, 1.0))
    return cv2.GaussianBlur(m, (0, 0), max(1.0, 0.035 * R.S * ras.s)) * k


def _head_paint(pen, ink, R, hd, who, mode='full'):
    """按“遮挡 → 固有色 → 阴影 → 线 → 五官 → 发夹”的顺序交出指令。mode='sketch' 时只有线。"""
    S, f = R.S, R.f
    ras = R.raster
    girl_ = who == 'girl'
    sketch = mode == 'sketch'
    hm, fm, nm, em, cm = (ras.masks[k] for k in (_HAIR, _FACE, _NECK, _EAR, _COLLAR))
    skin = np.clip(fm + nm + em, 0, 1)
    allm = np.clip(skin + hm + cm, 0, 1)
    hair_c = 'hair' if girl_ else 'boy_hair'
    col_c = 'sweater' if girl_ else 'boy_shirt'
    seed = R.seed + 100
    e = R.face
    if not sketch:
        # ---- 遮挡 + 固有色
        ras.emit(pen, 'cover', allm, seed=seed + 1, feather=1.0)
        ras.emit(pen, 'fill', skin, color='skin', seed=seed + 2, b_layers=2, b_clean=True)
        # 体积：背光一侧（来自 3D 法线）、刘海/鬓发投在脸上的影、颧骨下、下巴投在脖子上的影（都很轻）
        fe = np.clip(fm + em, 0, 1)
        ras.emit(pen, 'shade', ras.shade * fe, amount=0.20 if girl_ else 0.22, seed=seed + 3, angle=60,
                 color='skin_sh')
        dn = -R.head_up * ras.s
        hs = _shift(hm, dn * 0.030 * S)
        near_hair = np.clip(cv2.GaussianBlur(hs, (0, 0), max(1.0, 0.028 * S * ras.s)) * 1.3, 0, 1) * fm
        ras.emit(pen, 'shade', near_hair, amount=0.26, seed=seed + 4, color='skin_sh')
        if girl_ and not R.back:
            hol = _cheek_hollow(R, ras)
            if hol is not None:
                ras.emit(pen, 'shade', hol * fm, amount=0.11, seed=seed + 15, color='skin_sh', angle=70)
        ras.emit(pen, 'shade', em, amount=0.22, seed=seed + 16, color='skin_sh', angle=60)
        jaw = np.clip(cv2.GaussianBlur(_shift(fm, dn * 0.075 * S), (0, 0), max(1.0, 0.03 * S * ras.s)) * 1.4, 0, 1)
        ras.emit(pen, 'shade', nm * np.clip(0.25 + 0.30 * ras.shade + 0.75 * jaw, 0, 1), amount=0.34, seed=seed + 5,
                 angle=70, color='skin_sh')
        # 领子
        ras.emit(pen, 'cover', cm, seed=seed + 6, feather=0.8)
        ras.emit(pen, 'fill', cm, color=col_c, seed=seed + 7)
        ras.emit(pen, 'shade', cm * (0.35 + 0.65 * ras.shade), amount=0.14, seed=seed + 8, angle=80)
        # 头发
        ras.emit(pen, 'cover', hm, seed=seed + 9, feather=0.8)
        ras.emit(pen, 'fill', hm, color=hair_c, seed=seed + 10, streak=0.45, bloom=0.3)
        ras.emit(pen, 'shade', hm * ras.shade, amount=0.28, seed=seed + 11, angle=65)
    elif mode == 'sketch':
        # 草稿：头发只排几笔线
        ras.emit(pen, 'hatch', hm * 0.9, angle=55 if f > 0 else 125, spacing=6.5, tone=0.42 * (1 - 0.5 * R.erase),
                 color='graphite', seed=seed + 12, partial=0.3)

    lrole = 'sketch' if sketch else 'contour'
    drole = 'sketch' if sketch else 'detail'
    lc = 'graphite' if sketch else None
    # ---- 轮廓：头发外形
    if girl_ and not sketch:
        # 外形（挨着纸/领子）一笔重的；压在脸上的刘海、鬓发下沿轻一些、细一些（参差才看得出来）
        for k, (P, closed) in enumerate(ras.outline([_HAIR], [0, _COLLAR, _NECK], min_len=10)):
            ink.line(P, 0.030 * S, tone=0.85, seed=(seed + 20, k), role=lrole, color=hair_c, closed=closed,
                     taper=(0.15, 0.25), clip=False, dry=0.4, dry_from=0.6, head=0.2)
        for k, (P, closed) in enumerate(ras.outline([_HAIR], [_FACE, _EAR], min_len=5, smooth=1)):
            ink.line(P, 0.017 * S, tone=0.72, seed=(seed + 24, k), role=lrole, color=hair_c, closed=closed,
                     taper=(0.2, 0.2), clip=False, head=0.1)
    else:
        for k, (P, closed) in enumerate(ras.outline([_HAIR], [0, _FACE, _NECK, _COLLAR, _EAR], min_len=10)):
            ink.line(P, 0.030 * S, tone=0.85, seed=(seed + 20, k), role=lrole, color=hair_c if not sketch else lc,
                     closed=closed, taper=(0.15, 0.25), clip=False, dry=0.4, dry_from=0.6, head=0.2)
    # 脸的外轮廓（挨着纸或脖子的部分）：近侧的下颌线清楚，远侧（鼻子那一侧）的脸颊轮廓轻一些
    hc0 = R.proj(np.float32([[0.0, 0.10, 0.0]]))[0]
    nd = _unit(R.proj(np.float32([[0.0, 0.10, 0.5]]))[0] - hc0)
    nlen = float(np.hypot(*(R.proj(np.float32([[0.0, 0.10, 0.5]]))[0] - hc0))) / (0.5 * S)
    for k, (P, closed) in enumerate(ras.outline([_FACE], [0, _NECK, _COLLAR], min_len=6)):
        if nlen < 0.25 or sketch:
            ink.line(P, 0.018 * S, tone=0.55, seed=(seed + 30, k), role=lrole, color=lc, closed=closed,
                     taper=(0.3, 0.4), clip=False, fade=0.2)
            continue
        far = ((P - hc0) @ nd) > 0.16 * S
        for j, (a_, b_, ca, cb) in enumerate(_runs(P, far, min_pts=2)):
            ink.line(P[max(0, a_ - 1):b_ + 1], 0.016 * S, tone=0.40, seed=(seed + 30, k, 1, j), role=lrole,
                     color=lc, taper=(0.35, 0.35), clip=False, fade=0.15)
        for j, (a_, b_, ca, cb) in enumerate(_runs(P, ~far, min_pts=2)):
            ink.line(P[a_:b_], 0.021 * S, tone=0.66, seed=(seed + 30, k, 2, j), role=lrole, color=lc,
                     taper=(0.3, 0.35), clip=False, head=0.2)
    # 耳朵
    for k, (P, closed) in enumerate(ras.outline([_EAR], [0, _FACE, _NECK], min_len=5)):
        ink.line(P, 0.016 * S, tone=0.5, seed=(seed + 40, k), role=lrole, color=lc, closed=closed,
                 taper=(0.3, 0.4), clip=False)
    for es, rim, base in hd['ears']:
        p3 = np.float32([(rim[2] * 0.6 + base[2] * 0.4), (rim[4] * 0.55 + base[4] * 0.45),
                         (rim[6] * 0.6 + base[6] * 0.4)])
        p, z = R.proj(p3, with_z=True)
        vis = ras.sample(em, p)
        if vis.mean() > 0.5:
            ink.line(p, 0.012 * S, tone=0.38, seed=seed + 45 + (es > 0), role=drole, color=lc,
                     taper=(0.3, 0.4), clip=False)
    # 脖子（挨着纸的边）
    for k, (P, closed) in enumerate(ras.outline([_NECK], [0], min_len=6)):
        ink.line(P, 0.020 * S, tone=0.55, seed=(seed + 50, k), role=lrole, color=lc, closed=closed,
                 taper=(0.25, 0.35), clip=False, dry=0.3)
    # 领子
    for k, (P, closed) in enumerate(ras.outline([_COLLAR], [0, _NECK, _FACE], min_len=8)):
        ink.line(P, 0.026 * S, tone=0.70, seed=(seed + 60, k), role=lrole, color=lc, closed=closed,
                 taper=(0.15, 0.4), clip=False, head=0.4, dry=0.4, dry_from=0.6)
    if girl_:
        # 高领翻折的那道线
        fold = R.TB([(-0.27, -0.07), (-0.02, -0.085), (0.22, -0.11)])
        ink.line(fold, 0.022 * S, tone=0.42, seed=seed + 65, role=drole, color=lc, clip=False,
                 keep=lambda P: (ras.sample(cm, P) > 0.4), dry=0.6, dry_from=0.4)

    # ---- 发丝：顺发流的笔触（只在可见头发上）
    hd_keep = lambda P: ras.sample(hm, P) > 0.55
    Ph, Zh, ry, keep, fch = hd['Ph'], hd['Zh'], hd['ry'], hd['keep'], hd['fch']
    nphi = Ph.shape[1]
    rr = rng(R.seed, 600)
    widths = rr.uniform(0.8, 1.2, nphi)
    tones = rr.uniform(0.30, 0.55, nphi)
    step = 4 if girl_ else 6
    if sketch:
        step = 4 if girl_ else 8
    for i in range(0, nphi, step):
        if Zh[len(ry) // 2, i] < -0.10 and Zh[3, i] < -0.10 and Zh[-2, i] < -0.10:
            continue
        kc = keep[:, i].astype(np.int8)
        edges = np.flatnonzero(np.diff(np.concatenate([[0], kc, [0]])))
        for ri, (ja, jz) in enumerate(zip(edges[0::2], edges[1::2])):
            ja = max(ja, 1)
            pts = _dedupe(Ph[ja:jz, i], 0.012 * S)
            if len(pts) < 3:
                continue
            pts = pts[::2] if len(pts) > 6 else pts
            if len(pts) < 2:
                continue
            ink.line(pts, (0.075 if girl_ else 0.05) * S * widths[i], tone=float(tones[i]),
                     seed=(R.seed, 620 + i, ri), role=drole, color=hair_c if not sketch else lc,
                     taper=(0.05, 0.3), clip=False, keep=hd_keep, dry=0.85, dry_from=0.6, streak=0.5, fade=0.2)
    if girl_ and not sketch:
        # 头顶的光泽：两道弧形提白
        for k, (yy_, w_) in enumerate(((-0.40, 0.10), (-0.33, 0.06))):
            j = int(np.searchsorted(ry, yy_))
            idx = np.flatnonzero(Zh[j] > 0.08)
            if len(idx) > 4:
                seg_ = Ph[j][idx]
                seg_ = seg_[np.argsort(seg_[:, 0])]
                seg_ = seg_[int(len(seg_) * 0.12):int(len(seg_) * (0.80 - 0.15 * k))]
                if len(seg_) > 3:
                    poly, _, _ = tube(seg_[::2], [w_ * S * 0.3, w_ * S, w_ * S * 0.3])
                    Mh = _poly_mask_screen(ras, poly) * hm
                    ras.emit(pen, 'lift', Mh, amt=0.38, seed=seed + 760 + k, soft=2.0, dry=0.9, streak=0.6)
    if not girl_:
        # 他：头顶两根翘毛 + 往前扫的几缕
        for k in range(2):
            root = R.proj(np.float32([[-0.05 - 0.16 * k, -0.58 + 0.03 * k, -0.04 - 0.12 * k]]))[0]
            ink.line([root, root + np.float32([(-0.05 + 0.08 * k) * f * S, -0.09 * S])], 0.022 * S, tone=0.6,
                     seed=seed + 25 + k, role=drole, color=hair_c if not sketch else lc, taper=(0.1, 0.7),
                     clip=False)
        for k in range(4 if not R.back_view else 0):
            root = R.proj(np.float32([[-0.28 + 0.09 * k, -0.55 + 0.02 * k, -0.1 + 0.06 * k]]))[0]
            tip = R.proj(np.float32([[0.30 - 0.04 * k, -0.17 - 0.03 * k + (0.03 if k % 2 else 0), 0.36 - 0.04 * k]]))[0]
            midp = (root + tip) / 2 + R.head_up * 0.05 * S
            ink.line([root, midp, tip], 0.022 * S, tone=0.55, seed=seed + 27 + k, role=drole,
                     color=hair_c if not sketch else lc, taper=(0.1, 0.7), clip=False,
                     keep=(None if sketch else hd_keep))
        # 轮廓上翘出来的几根碎发（微乱）：从头发外轮廓上长出来，短、带一点弯
        hc_ = R.proj(np.float32([[0.0, -0.10, 0.0]]))[0]
        outs = [P for P, _ in ras.outline([_HAIR], [0], min_len=20)]
        if outs:
            P = max(outs, key=len)
            top = P[P[:, 1] < hc_[1] - 0.05 * S]
            if len(top) > 8:
                rr_ = rng(R.seed, 640)
                for k, tt in enumerate((0.12, 0.34, 0.58, 0.83)):
                    p0 = top[int(tt * (len(top) - 1))]
                    dv = _unit(p0 - hc_)
                    tv = _perp(dv) * (1 if k % 2 else -1)
                    L_ = (0.030 + 0.018 * rr_.random()) * S
                    ink.line([p0 - dv * 0.025 * S, p0 + dv * L_ * 0.55 + tv * L_ * 0.20,
                              p0 + dv * L_ + tv * L_ * 0.55], 0.015 * S, tone=0.6, seed=seed + 70 + k, role=drole,
                             color=hair_c if not sketch else lc, taper=(0.2, 0.8), clip=False)
        if not sketch:
            # 光泽：头顶一道弧形提白
            j = int(np.searchsorted(ry, -0.40))
            idx = np.flatnonzero(Zh[j] > 0.10)
            if len(idx) > 4:
                seg_ = Ph[j][idx]
                seg_ = seg_[np.argsort(seg_[:, 0])]
                seg_ = seg_[int(len(seg_) * 0.18):int(len(seg_) * 0.70)]
                if len(seg_) > 3:
                    poly, _, _ = tube(seg_[::2], [0.02 * S, 0.06 * S, 0.02 * S])
                    Mh = _poly_mask_screen(ras, poly) * hm
                    ras.emit(pen, 'lift', Mh, amt=0.30, seed=seed + 765, soft=2.0, dry=0.9, streak=0.6)

    # ---- 五官
    if not R.back:
        sty = GIRL_FEAT if girl_ else BOY_FEAT
        if not sketch:
            _blush(ink, R, e, sty)
        eyes = [_eye(ink, R, s_, e, sty) if not sketch else None for s_ in (-1, 1)]
        if sketch:
            _sketch_face(ink, R, e, sty)
        else:
            for s_ in (-1, 1):
                _brow(ink, R, s_, e, sty)
            _nose(ink, R, sty)
            _mouth(ink, R, e, sty)
            _tear(ink, R, e, sty, eyes)
        R.eyes = eyes
    if girl_:
        _hairpin(pen, ink, R)


def _sketch_face(ink, R, e, sty):
    """草稿的五官：几笔铅笔线（眼 = 弯弧 + 一点，眉、鼻、嘴）。和 full 用同一组面上的点。"""
    S, tab = R.S, R.face_tab
    sm = float(e.get('smile', 0.0))
    op = float(e.get('open', 0.8))
    happy = float(e.get('happy', 0.0))
    keep = R.keep_face
    for side in (-1, 1):
        inner3 = _surf(tab, sty['y_in'], sty['ph_in'] * side)
        outer3 = _surf(tab, sty['y_out'], sty['ph_out'] * side)
        (pi, po), z = R.proj(np.float32([inner3, outer3]), with_z=True)
        if float(z.mean()) < 0.03:
            continue
        e1 = _unit(po - pi)
        up = _perp(e1)
        if float(np.dot(up, R.head_up)) < 0:
            up = -up
        L = float(np.hypot(*(po - pi)))
        if op < 0.18 or happy > 0.6:
            arc = [pi, pi + e1 * 0.5 * L + up * 0.032 * S * (1 if happy > 0.5 else -0.6), po]
        else:
            arc = [pi, pi + e1 * 0.5 * L + up * sty['hu'] * S * min(op, 1.0), po]
        ink.line(arc, 0.024 * S, tone=0.85, seed=R.seed + 900 + (side > 0), role='sketch', color='graphite',
                 clip=False, keep=keep, spread=0.9)
        if op >= 0.18 and happy <= 0.6:
            c = pi + e1 * 0.5 * L + up * sty['hu'] * S * 0.25
            ink.line([c - up * 0.012 * S, c + up * 0.012 * S], 0.026 * S, tone=0.8, seed=R.seed + 905 + (side > 0),
                     role='sketch', color='graphite', clip=False, reps=1)
        # 下眼睑（笑眼）
        lid = [pi + e1 * 0.15 * L - up * 0.03 * S, pi + e1 * 0.5 * L - up * 0.036 * S, po - up * 0.025 * S]
        ink.line(lid, 0.013 * S, tone=0.45, seed=R.seed + 910 + (side > 0), role='sketch', color='graphite',
                 clip=False, keep=keep, reps=1)
        _brow(ink, R, side, e, dict(sty, brow_c='graphite'))
    _nose(ink, R, sty)
    mo = [_surf(tab, sty['mouth_y'] - 0.03 * sm, -sty['mouth_ph'] - 3), _surf(tab, sty['mouth_y'] + 0.01, -4),
          _surf(tab, sty['mouth_y'] + 0.01, 4), _surf(tab, sty['mouth_y'] - 0.035 * sm, sty['mouth_ph'] + 3)]
    p, z = R.proj(np.stack(mo), with_z=True)
    if float(z.mean()) > 0.0:
        ink.line(p, 0.022 * S, tone=0.85, seed=R.seed + 914, role='sketch', color='graphite', clip=False, keep=keep,
                 spread=0.8)
        cheek = R.proj(np.stack([_surf(tab, 0.20, 30), _surf(tab, 0.27, 28)]))
        ink.line(cheek, 0.014 * S, tone=0.4, seed=R.seed + 918, role='sketch', color='graphite', clip=False,
                 keep=keep, reps=1)


def _hairpin(pen, ink, R):
    """红豆发夹：PIN_SIDE 那一侧（模型 x 符号 ts）耳朵上方，别住耳后的头发。任何笔刷下都是红色。
    位置略靠后：正面 3/4 看在近侧时清楚；从背后看在头发轮廓边上露出一点。"""
    S = R.S
    p3 = np.float32([[0.392 * R.ts, -0.085, 0.020]])
    cp = R.proj(p3)
    nz = (R.proj.R @ _unit(np.float32([R.ts * 0.98, 0.0, 0.05])))[2]
    if float(nz) < -0.22:
        return
    cx, cy = cp[0]
    rot = -25 * R.f
    k = R.f
    with pen.group('hairpin', boil=0.25):
        pen.cover(ell(cx, cy, 0.064 * S, 0.050 * S, rot=rot), seed=R.seed + 905, feather=0.8)
        pen.fill(ell(cx, cy, 0.055 * S, 0.040 * S, rot=rot, n=20), 'hairpin', seed=R.seed + 900)
        pen.shade(ell(cx + 0.012 * S * k, cy + 0.012 * S, 0.034 * S, 0.022 * S, rot=rot, n=14), amount=0.35,
                  seed=R.seed + 901, color='bean_d')
        pen.line(ell(cx, cy, 0.055 * S, 0.040 * S, rot=rot, n=20), 0.012 * S, tone=0.8, color='bean_d',
                 seed=R.seed + 902, closed=True, role='detail', taper=(0.0, 0.0))
        pen.lift(ell(cx - 0.02 * S * k, cy - 0.014 * S, 0.013 * S, 0.009 * S, n=10), amt=0.85, seed=R.seed + 903,
                 soft=0.5)
        # 金属夹子：一小笔
        pen.line([(cx - 0.08 * S * k, cy + 0.035 * S), (cx - 0.02 * S * k, cy + 0.014 * S)], 0.013 * S, tone=0.6,
                 color='metal', seed=R.seed + 904, role='detail', taper=(0.2, 0.2))


# =========================================================================== 手
def _hand(ink, R, wrist, hand, shape='fist', thumb=1, seed=0, color='skin', tone_line=0.6, role='contour',
          fill=True, size=1.0):
    """手：腕 wrist → 掌心 hand 的方向为手指方向。shape: fist 握拳/握柄、open 张开、flat 平放/按、cup 捧。
    thumb=±1：拇指在手指方向的哪一侧（屏幕上的法向）。返回 (外形多边形, 指尖点)。"""
    S = R.S * size
    hv = np.float32(hand) - np.float32(wrist)
    Lh = float(np.hypot(*hv)) + 1e-6
    d = hv / Lh
    n = _perp(d) * thumb
    w = np.float32(wrist)
    if shape == 'fist':
        out = [w + n * 0.065 * S, w + d * 0.05 * S + n * 0.075 * S, w + d * 0.15 * S + n * 0.06 * S,
               w + d * 0.19 * S + n * 0.0 * S, w + d * 0.16 * S - n * 0.07 * S, w + d * 0.05 * S - n * 0.075 * S,
               w - n * 0.065 * S]
        thumb_p = [w + d * 0.05 * S + n * 0.07 * S, w + d * 0.12 * S + n * 0.09 * S, w + d * 0.17 * S + n * 0.05 * S,
                   w + d * 0.14 * S + n * 0.035 * S, w + d * 0.07 * S + n * 0.045 * S]
        fingers = [[w + d * (0.17 - 0.0) * S - n * 0.02 * S, w + d * 0.12 * S - n * 0.03 * S],
                   [w + d * 0.155 * S - n * 0.05 * S, w + d * 0.11 * S - n * 0.055 * S]]
        tip = w + d * 0.19 * S
    elif shape == 'open':
        out = [w + n * 0.06 * S, w + d * 0.11 * S + n * 0.075 * S, w + d * 0.22 * S + n * 0.05 * S,
               w + d * 0.27 * S + n * 0.0 * S, w + d * 0.25 * S - n * 0.05 * S, w + d * 0.12 * S - n * 0.07 * S,
               w - n * 0.06 * S]
        thumb_p = [w + d * 0.05 * S + n * 0.06 * S, w + d * 0.10 * S + n * 0.13 * S, w + d * 0.15 * S + n * 0.16 * S,
                   w + d * 0.15 * S + n * 0.12 * S, w + d * 0.10 * S + n * 0.07 * S]
        fingers = [[w + d * 0.15 * S + n * 0.025 * S, w + d * 0.26 * S + n * 0.03 * S],
                   [w + d * 0.15 * S - n * 0.01 * S, w + d * 0.265 * S - n * 0.012 * S],
                   [w + d * 0.14 * S - n * 0.04 * S, w + d * 0.24 * S - n * 0.045 * S]]
        tip = w + d * 0.27 * S
    elif shape == 'cup':
        out = [w + n * 0.06 * S, w + d * 0.10 * S + n * 0.08 * S, w + d * 0.20 * S + n * 0.07 * S,
               w + d * 0.25 * S + n * 0.03 * S, w + d * 0.24 * S - n * 0.03 * S, w + d * 0.12 * S - n * 0.07 * S,
               w - n * 0.06 * S]
        thumb_p = [w + d * 0.06 * S + n * 0.06 * S, w + d * 0.13 * S + n * 0.10 * S, w + d * 0.17 * S + n * 0.09 * S,
                   w + d * 0.12 * S + n * 0.06 * S]
        fingers = [[w + d * 0.15 * S + n * 0.03 * S, w + d * 0.23 * S + n * 0.035 * S],
                   [w + d * 0.15 * S - n * 0.01 * S, w + d * 0.235 * S - n * 0.01 * S]]
        tip = w + d * 0.25 * S
    else:   # flat
        out = [w + n * 0.06 * S, w + d * 0.12 * S + n * 0.07 * S, w + d * 0.24 * S + n * 0.05 * S,
               w + d * 0.28 * S + n * 0.01 * S, w + d * 0.26 * S - n * 0.045 * S, w + d * 0.12 * S - n * 0.065 * S,
               w - n * 0.06 * S]
        thumb_p = [w + d * 0.05 * S + n * 0.06 * S, w + d * 0.12 * S + n * 0.10 * S, w + d * 0.16 * S + n * 0.10 * S,
                   w + d * 0.13 * S + n * 0.065 * S]
        fingers = [[w + d * 0.16 * S + n * 0.022 * S, w + d * 0.265 * S + n * 0.026 * S],
                   [w + d * 0.16 * S - n * 0.015 * S, w + d * 0.26 * S - n * 0.018 * S]]
        tip = w + d * 0.28 * S
    poly = spline(np.float32(out), 1.5, closed=True)
    tpoly = spline(np.float32(thumb_p), 1.5, closed=True)
    if fill:
        ink.cover([poly, tpoly], seed=seed, feather=0.7)
        ink.fill([poly, tpoly], color, seed=seed + 1)
        ink.shade([np.vstack([poly[len(poly) // 2:], [w]])], amount=0.18, seed=seed + 2, color='skin_sh')
    ink.line(np.float32(out), 0.020 * S, tone=tone_line, seed=seed + 3, role=role, closed=False, taper=(0.2, 0.4),
             color=None if role != 'sketch' else 'graphite')
    ink.line(np.float32(thumb_p[:-1]), 0.018 * S, tone=tone_line * 0.9, seed=seed + 4, role=role, taper=(0.2, 0.5),
             color=None if role != 'sketch' else 'graphite')
    for k, fp in enumerate(fingers):
        ink.line(np.float32(fp), 0.011 * S, tone=tone_line * 0.6, seed=seed + 5 + k,
                 role='detail' if role != 'sketch' else 'sketch', taper=(0.3, 0.5),
                 color=None if role != 'sketch' else 'graphite', reps=1)
    return poly, tip


# =========================================================================== 手臂姿态
def arm_stir(t, args, rig=None):
    """搅锅：勺头在汤面上画椭圆，手握在勺柄上端跟着画圈；一圈 period 秒（t0 为相位偏移，单位圈）。"""
    cx, cy, rx, ry = args['soup']
    per = args.get('period', 1.75)
    th = 2 * math.pi * (t - args.get('t0', 0.0)) / per
    tip = np.float32([cx + 0.48 * rx * math.cos(th), cy + 0.42 * ry * math.sin(th)])
    off = np.float32(args.get('handle', (-82, -52)))
    hand = tip + off + np.float32([5 * math.cos(th + 0.5), 3 * math.sin(th + 0.5)])
    return dict(near=dict(hand=hand, shape='fist', tool=('spoon', tip), thumb=-1), far=None)


def arm_rest(t, args, rig=None):
    """手搭在台面/桌面上：hand（场景坐标），shape 默认 flat。"""
    return dict(near=dict(hand=np.float32(args['hand']), shape=args.get('shape', 'flat'), tool=None,
                          thumb=args.get('thumb', -1)), far=None)


def arm_reach(t, args, rig=None):
    """伸手：从 start 伸向 target，u 0..1（缓入缓出）。"""
    u = float(smooth01(args.get('u', 1.0)))
    return dict(near=dict(hand=lerp(args['start'], args['target'], u), shape='open', tool=None,
                          thumb=args.get('thumb', -1)), far=None)


def arm_wipe_tear(t, args, rig=None):
    """手指背擦泪：手停在近侧眼下，轻轻来回。eye 不写就用她自己的近侧眼位置（rig 算）。u 0..1 抬手进度。"""
    if 'eye' in args:
        eye = np.float32(args['eye'])
    else:
        eye = rig.eye_guess()
    u = float(smooth01(args.get('u', 1.0)))
    S = rig.S
    rest = rig.TB([(-0.10, 1.3)])[0]
    tgt = eye + np.float32([-0.04 * S * rig.f + 0.02 * S * math.sin(t * 5), 0.16 * S])
    return dict(near=dict(hand=lerp(rest, tgt, u), shape='fist', tool=None, thumb=1, bend=-rig.f,
                          wrist_up=True), far=None)


def arm_hold(t, args, rig=None):
    """双手捧着碗/杯：at 中心（场景坐标），r 半径，what='bowl'|'cup'。"""
    S = rig.S
    at = np.float32(args.get('at', rig.TB([(0.55, 0.95)])[0]))
    r = float(args.get('r', 0.22 * S))
    what = args.get('what', 'bowl')
    near = dict(hand=at + np.float32([-0.55 * r * rig.f, 0.25 * r]), shape='cup', thumb=1, tool=(what, at, r))
    far = dict(hand=at + np.float32([0.75 * r * rig.f, 0.15 * r]), shape='cup', thumb=-1, front=True)
    return dict(near=near, far=far)


def arm_hug_self(t, args, rig=None):
    """抱臂：两前臂交叉在胸前，手搭在对侧上臂。"""
    near = dict(hand=rig.TB([(0.36, 0.62)])[0], shape='flat', thumb=-1, bend=rig.f)
    far = dict(hand=rig.TB([(-0.42, 0.72)])[0], shape='flat', thumb=1, front=True, bend=rig.f)
    return dict(near=near, far=far)


def arm_hand_chest(t, args, rig=None):
    """手按胸口（u 0..1 抬手进度）。"""
    u = float(smooth01(args.get('u', 1.0)))
    rest = rig.TB([(-0.10, 1.3)])[0]
    tgt = rig.TB([(0.10, 0.48)])[0]
    return dict(near=dict(hand=lerp(rest, tgt, u), shape='flat', thumb=1, bend=rig.f), far=None)


def arm_spoon_bowl(t, args, rig=None):
    """坐着用勺舀碗里的汤：bowl=(cx,cy) 碗口中心，lift 0..1 把勺抬起（喂/尝）。"""
    S = rig.S
    bc = np.float32(args['bowl'])
    lift = float(smooth01(args.get('lift', 0.0)))
    th = 2 * math.pi * t / args.get('period', 3.0)
    tip0 = bc + np.float32([0.10 * S * math.cos(th), 0.02 * S * math.sin(th)])
    tip1 = np.float32(args.get('to', bc + np.float32([0.1 * S * rig.f, -0.8 * S])))
    tip = lerp(tip0, tip1, lift)
    hand = tip + np.float32([-0.55 * S * rig.f, -0.25 * S])
    return dict(near=dict(hand=hand, shape='fist', tool=('spoon', tip), thumb=-1), far=None)


ARM_POSES = {'stir': arm_stir, 'rest': arm_rest, 'reach': arm_reach, 'wipe_tear': arm_wipe_tear,
             'hold': arm_hold, 'hug_self': arm_hug_self, 'hand_chest': arm_hand_chest,
             'spoon_bowl': arm_spoon_bowl}


# =========================================================================== 她
class _GirlRig:
    def __init__(self, pose):
        self.pose = pose
        self.S = S = float(pose.get('s', 110))
        self.back = bool(pose.get('back', False))
        # 背影：人朝画面里面，facing 不起作用（她的右侧在画面右边）
        self.f = f = 1 if (self.back or pose.get('facing', 1) >= 0) else -1
        self.ts = f if PIN_SIDE == 'left' else -f     # 发夹那一侧在头部模型里的 x 符号（模型 +x = 她的左侧 × f）
        self.tilt = float(pose.get('tilt', 0.0))
        self.seed = int(pose.get('seed', 1000))
        self.boil = float(pose.get('boil', 1.0))
        br = math.sin(2 * math.pi * pose.get('breath', 0.0))
        self.br = br
        self.N0 = np.float32([pose['x'], pose['y'] - 0.6 * br])
        self.lean = float(pose.get('lean', 0.0))
        self.body = pose.get('body', 'upper')
        self.back = bool(pose.get('back', False))
        self.light = float(pose.get('light', 1.0))
        self.erase = 0.0
        self.face_tab = GIRL_FACE
        self.face = _face_of(pose.get('face'))
        self.face['open'] = self.face['open'] * (1.0 - float(pose.get('blink', 0.0)))
        hip_v = 1.55
        self.hip_v = hip_v
        piv = self.TB([(0.0 if self.back else 0.05, -0.42)])[0]
        yaw = pose.get('yaw', 180 if self.back else 40)
        self.proj = HeadProj(piv, S, yaw, pose.get('pitch', 0), pose.get('roll', 0), flip=f)
        hu = self.proj(np.float32([[0, -0.2, 0.3]]))[0] - self.proj(np.float32([[0, 0.2, 0.3]]))[0]
        self.head_up = _unit(hu)
        self.keep_face = None
        self.eyes = [None, None]
        self.clip = _Clipper(pose.get('clip_y'), pose.get('clip_poly'))

    def T(self, pts):
        p = np.asarray(pts, np.float32).reshape(-1, 2)
        return np.stack([self.N0[0] + self.f * p[:, 0] * self.S, self.N0[1] + p[:, 1] * self.S], 1)

    def TB(self, pts):
        """上身：以臀部为轴前倾（背影时 u 是横向，tilt 度：上身以臀部为轴往画面右侧歪）。"""
        p = np.asarray(pts, np.float32).reshape(-1, 2).copy()
        if self.back:
            if self.tilt:
                th = math.radians(self.tilt)
                c_, s_ = math.cos(th), math.sin(th)
                dx, dy = p[:, 0].copy(), p[:, 1] - self.hip_v
                p[:, 0] = dx * c_ - dy * s_
                p[:, 1] = dx * s_ + dy * c_ + self.hip_v
            return self.T(p)
        p[:, 0] += self.lean * np.clip(self.hip_v - p[:, 1], 0, None) * 0.25
        return self.T(p)

    def eye_guess(self):
        p3 = _surf(GIRL_FACE, GIRL_FEAT['y_in'], -28)
        p3b = _surf(GIRL_FACE, GIRL_FEAT['y_in'], 28)
        (a, b), z = self.proj(np.stack([p3, p3b]), with_z=True)
        return a if z[0] >= z[1] else b

    # ---------------------------------------------------------------- 轮廓（身体）
    def torso(self):
        front = [(0.15, -0.04), (0.30, 0.08), (0.39, 0.28), (0.45, 0.48), (0.40, 0.69), (0.32, 0.93),
                 (0.30, 1.15), (0.35, 1.38), (0.40, 1.56)]
        back = [(-0.17, -0.08), (-0.37, 0.03), (-0.53, 0.15), (-0.60, 0.38), (-0.57, 0.68), (-0.49, 0.98),
                (-0.45, 1.18), (-0.50, 1.40), (-0.54, 1.57)]
        hem = [(-0.30, 1.61), (0.0, 1.62), (0.22, 1.60)]
        return front, back, hem

    def silhouette(self):
        front, back, hem = self.torso()
        sil = spline(self.TB([(-0.08, -0.15), (0.12, -0.17)] + front + hem[::-1] + back[::-1]), 4.0, closed=True)
        head = cv2.convexHull(self.proj(_hair_shell_girl(self.seed, self.ts)[1].reshape(-1, 3)).astype(np.float32))
        out = [sil, head.reshape(-1, 2)]
        if self.body == 'stand':
            out.append(self.T([(-0.47, 1.2), (0.31, 1.2), (0.60, 3.3), (-0.70, 3.35)]))
        return out


def _sleeve(ink, R, shp, elb, wr, hand, spec, seed, colors, role_c='contour', role_d='detail', fill=True,
            under_side=1, lc=None):
    """一只袖子（肩→肘→腕）+ 手。colors=(袖子固有色, 手色)。under_side=±1 袖子下侧在哪边。"""
    S = R.S
    f = R.f
    path = [shp, (shp + elb) / 2 + np.float32([0, 0.03 * S]), elb, (elb + wr) / 2, wr]
    poly, Ls, Rs = tube(path, [0.30 * S, 0.29 * S, 0.25 * S, 0.22 * S, 0.20 * S] if colors[0] == 'sweater'
                        else [0.32 * S, 0.31 * S, 0.27 * S, 0.24 * S, 0.22 * S])
    cap = ell(shp[0], shp[1], 0.18 * S, 0.17 * S, n=24)
    under = Rs if under_side > 0 else Ls
    top_ = Ls if under_side > 0 else Rs
    mids = spline(path, 2.0)
    if fill:
        # 填色按上臂、前臂两节分别成形（手臂折得很弯时单根管子会自交、填色出现空洞）
        wd0 = 0.30 if colors[0] == 'sweater' else 0.32
        up_p, _, _ = tube([shp, (shp + elb) / 2 + np.float32([0, 0.03 * S]), elb], [wd0 * S, (wd0 - 0.01) * S,
                                                                                  (wd0 - 0.05) * S])
        fo_p, _, _ = tube([elb, (elb + wr) / 2, wr], [(wd0 - 0.05) * S, (wd0 - 0.08) * S, (wd0 - 0.10) * S])
        ecap = ell(elb[0], elb[1], (wd0 - 0.05) * S / 2, (wd0 - 0.05) * S / 2, n=18)
        ink.cover([up_p, fo_p, cap, ecap], seed=seed + 33, feather=0.9)
        ink.fill([up_p, fo_p, cap, ecap], colors[0], seed=seed + 34)
        ink.shade([np.vstack([under, mids[::-1]])], amount=0.32, seed=seed + 35, angle=20 if f > 0 else 160)
    n_t = len(top_)
    ink.line(top_[2:int(n_t * 0.55):6], 0.050 * S, tone=0.86, seed=seed + 36, role=role_c, color=lc,
             taper=(0.12, 0.3), head=0.5, lift=0.3, dry=0.5, dry_from=0.6, streak=0.25, pool=0.2)
    ink.line(top_[int(n_t * 0.5):-2:6], 0.042 * S, tone=0.80, seed=seed + 37, role=role_c, color=lc,
             taper=(0.2, 0.35), head=0.35, lift=0.2, dry=0.5, dry_from=0.55, streak=0.2)
    n_u = len(under)
    ink.line(under[int(n_u * 0.12):int(n_u * 0.52):6], 0.040 * S, tone=0.72, seed=seed + 38, role=role_c, color=lc,
             taper=(0.3, 0.3), head=0.3, dry=0.5, dry_from=0.5, streak=0.25)
    ink.line(under[int(n_u * 0.55):-3:6], 0.034 * S, tone=0.66, seed=seed + 39, role=role_c, color=lc,
             taper=(0.3, 0.3), head=0.25, dry=0.4, dry_from=0.6)
    # 肩头圆弧（朝外的那一侧）
    ov = _unit(shp - elb)
    a0 = math.degrees(math.atan2(ov[1], ov[0]))
    ink.line(ell(shp[0], shp[1], 0.18 * S, 0.17 * S, a0 - 70, a0 + 40, 10), 0.045 * S, tone=0.82, seed=seed + 47,
             role=role_c, color=lc, taper=(0.3, 0.3), head=0.4)
    # 肘部褶皱
    fv = _unit(wr - elb)
    nv = _perp(fv) * under_side
    for k, o in enumerate((0.05, 0.14)):
        p0 = elb + fv * o * S + nv * 0.05 * S
        ink.line([p0, p0 + fv * 0.05 * S - nv * 0.04 * S, p0 + fv * 0.06 * S - nv * 0.09 * S], 0.020 * S, tone=0.5,
                 seed=seed + 40 + k, role=role_d, color=lc, taper=(0.3, 0.6), head=0.2, dry=0.5, dry_from=0.4)
    # 袖口
    c0 = wr - fv * 0.05 * S
    nn = _perp(fv)
    ink.line([c0 + nn * 0.105 * S, c0 + fv * 0.012 * S, c0 - nn * 0.105 * S], 0.026 * S, tone=0.70, seed=seed + 42,
             role=role_c, color=lc, taper=(0.2, 0.3), head=0.3)
    return poly


def _hang(R, shp, l1, l2, fwd=0.06):
    """自然下垂的手：几乎伸直（肘微弯向后），fwd 往前一点。"""
    d = _unit(np.float32([fwd * R.f, 1.0]))
    return np.float32(shp) + d * (0.975 * (l1 + l2) + 0.10 * R.S)


def _arm_geom(R, shp, spec, l1, l2):
    hand = np.float32(spec['hand'])
    dv = hand - shp
    dist = float(np.hypot(*dv)) + 1e-6
    wr_t = hand - dv / dist * 0.10 * R.S
    if spec.get('wrist_up'):
        wr_t = hand + np.float32([0, 0.13 * R.S])
    bend = spec.get('bend', 1.0 if R.f > 0 else -1.0)
    elb, wr = ik2(shp, wr_t, l1, l2, bend=bend)
    return elb, wr, hand


def _tool_spoon(ink, R, hand, tip, seed, color='wood', role='contour', fill=True):
    S = R.S
    hv = _unit(hand - tip)
    top = hand + hv * 0.22 * S
    sp, sl, sr = tube([tip, (tip + hand) / 2, top], [0.030 * S, 0.038 * S, 0.044 * S])
    if fill:
        ink.pen.cover([sp], seed=seed, feather=0.6)
        ink.pen.fill([sp], color, seed=seed + 1)
    ink.line(sl[::6], 0.016 * S, tone=0.75, seed=seed + 2, role=role, taper=(0.1, 0.2), head=0.3, dry=0.4,
             dry_from=0.6, clip=False)
    ink.line(sr[::6], 0.011 * S, tone=0.45, seed=seed + 3, role=role, taper=(0.1, 0.2), clip=False)


def _tool_bowl(ink, R, c, r, seed, role='contour', fill=True, what='bowl'):
    """被捧着的碗（红豆汤）/杯。"""
    S = R.S
    cx, cy = float(c[0]), float(c[1])
    if what == 'cup':
        hgt = r * 1.1
        body = np.vstack([ell(cx, cy, r * 0.62, r * 0.16, 180, 360, 14), np.float32([[cx + r * 0.62, cy + hgt]]),
                          ell(cx, cy + hgt, r * 0.58, r * 0.14, 0, 180, 12)])
        if fill:
            ink.pen.cover([body], seed=seed, feather=0.7)
            ink.pen.fill([body], 'enamel', seed=seed + 1)
            ink.pen.fill([ell(cx, cy, r * 0.55, r * 0.12)], 'soup', seed=seed + 2)
        ink.line(ell(cx, cy, r * 0.62, r * 0.16), 0.016 * S, tone=0.8, seed=seed + 3, role=role, closed=True,
                 clip=False)
        ink.line(body[13:], 0.018 * S, tone=0.8, seed=seed + 4, role=role, clip=False)
        return
    rx, ry = r, r * 0.26
    body = np.vstack([ell(cx, cy, rx, ry, 180, 360, 16), np.float32([[cx + rx, cy]]),
                      bez((cx + rx, cy), (cx + rx * 0.9, cy + 0.7 * r), (cx + rx * 0.4, cy + 0.74 * r), 8),
                      bez((cx - rx * 0.4, cy + 0.74 * r), (cx - rx * 0.9, cy + 0.7 * r), (cx - rx, cy), 8)])
    if fill:
        ink.pen.cover([body], seed=seed, feather=0.7)
        ink.pen.fill([body], 'enamel', seed=seed + 1)
        ink.pen.shade([np.vstack([body[16:]])], amount=0.2, seed=seed + 5)
        ink.pen.fill([ell(cx, cy + 0.02 * r, rx * 0.86, ry * 0.75)], 'soup', seed=seed + 2)
        for k in range(6):
            a = k * 1.9
            ink.pen.dot(cx + rx * 0.5 * math.cos(a) * (0.3 + 0.1 * k), cy + ry * 0.4 * math.sin(a), 0.018 * S,
                        0.013 * S, 'bean', seed=seed + 10 + k, rot=k * 40)
    ink.line(ell(cx, cy, rx, ry), 0.016 * S, tone=0.82, seed=seed + 3, role=role, closed=True, clip=False)
    ink.line(body[17:], 0.020 * S, tone=0.82, seed=seed + 4, role=role, clip=False)


def _girl_body(pen, ink, R):
    S, f = R.S, R.f
    seed = R.seed
    front, back, hem = R.torso()
    TB, T = R.TB, R.T
    # ---------------- 腿 / 裙子（站、坐）
    if R.body == 'stand':
        _girl_legs_stand(pen, ink, R)
    elif R.body == 'sit':
        _girl_legs_sit(pen, ink, R)
    # ---------------- 上身（米白高领毛衣）
    sil = spline(TB([(-0.08, -0.15), (0.12, -0.17)] + front + hem[::-1] + back[::-1]), 3.0, closed=True)
    ink.cover([sil], seed=seed + 1, feather=1.0, jit=R.boil * 0.6)
    ink.fill([sil], 'sweater', seed=seed + 2)
    shade = np.vstack([TB(back[1:]), TB([(-0.02, 1.58), (0.0, 0.9), (-0.10, 0.4), (-0.15, 0.10)])])
    g0, g1 = TB([(-0.58, 0.6)])[0], TB([(0.05, 0.6)])[0]
    ink.shade([shade], amount=0.38, seed=seed + 3, angle=72 if f > 0 else 108,
              grad=(float(g0[0]), float(g0[1]), float(g1[0]), float(g1[1]), 1.0, 0.0))
    # 背：一笔长线——肩头起笔重按，行笔略提，下段干笔飞白
    ink.line(TB(back[1:]), 0.075 * S, tone=0.90, seed=seed + 10, taper=(0.10, 0.22), head=0.55, lift=0.35,
             dry=0.75, dry_from=0.5, fade=0.25, streak=0.25, pool=0.2)
    ink.line(TB(front[1:5]), 0.040 * S, tone=0.70, seed=seed + 11, taper=(0.2, 0.45), head=0.35, lift=0.2,
             streak=0.2)
    ink.line(TB(front[4:]), 0.045 * S, tone=0.62, seed=seed + 12, taper=(0.25, 0.3), head=0.3, dry=0.6,
             dry_from=0.4, streak=0.25, fade=0.3)
    ink.line(TB([(-0.12, -0.08), (-0.30, 0.0), (-0.48, 0.09), (-0.58, 0.22)]), 0.05 * S, tone=0.85, seed=seed + 13,
             taper=(0.15, 0.35), head=0.45, lift=0.2, dry=0.4, dry_from=0.7)
    ink.line(TB([(-0.54, 1.57)] + hem + [(0.40, 1.56)]), 0.040 * S, tone=0.70, seed=seed + 14, taper=(0.2, 0.3),
             head=0.3, dry=0.5, dry_from=0.5)
    # 毛衣褶
    ink.line(TB([(-0.36, 0.52), (-0.22, 0.62), (-0.08, 0.66)]), 0.03 * S, tone=0.35, seed=seed + 16,
             role='detail', taper=(0.3, 0.5), head=0.1, dry=0.7, dry_from=0.2, streak=0.3)
    ink.line(TB([(-0.40, 0.95), (-0.20, 1.02), (0.02, 1.0)]), 0.028 * S, tone=0.30, seed=seed + 17,
             role='detail', taper=(0.3, 0.5), head=0.1, dry=0.7, dry_from=0.2, streak=0.3)
    ink.line(TB([(-0.42, 1.38), (-0.25, 1.47), (-0.05, 1.50)]), 0.026 * S, tone=0.28, seed=seed + 18,
             role='detail', taper=(0.3, 0.5), head=0.1, dry=0.7, dry_from=0.2, streak=0.3)
    return [sil]


def _girl_legs_stand(pen, ink, R):
    S, f, T = R.S, R.f, R.T
    seed = R.seed + 300
    ph = float(R.pose.get('gait', 0.0))
    step = float(R.pose.get('step', 0.0 if 'gait' not in R.pose else 1.0))
    sw = 0.30 * step * math.sin(2 * math.pi * ph)
    legs = []
    for k, (u0, sgn) in enumerate(((0.12, -1), (-0.14, 1))):      # 远侧腿、近侧腿
        du = sgn * sw
        lift_ = 0.06 * step * max(0.0, math.cos(2 * math.pi * ph) * -sgn)
        hip = (u0 * 0.6, 1.70)
        knee = (u0 + du * 0.55, 3.0)
        ank = (u0 + du, 4.52 - lift_)
        P = T([hip, knee, ank])
        poly, Ls_, Rs_ = tube(P, [0.20 * S, 0.15 * S, 0.095 * S])
        shoe = T([(ank[0] - 0.08, ank[1] - 0.04), (ank[0] + 0.05, ank[1] - 0.05), (ank[0] + 0.27, ank[1] + 0.07),
                  (ank[0] + 0.30, ank[1] + 0.16), (ank[0] - 0.09, ank[1] + 0.17)])
        legs.append((k, poly, Ls_, Rs_, shoe))
    for k, poly, Ls_, Rs_, shoe in legs:
        ink.cover([poly], seed=seed + k, feather=0.8)
        ink.fill([poly], TIGHTS, seed=seed + 2 + k)
        if k == 0:
            ink.shade([poly], amount=0.25, seed=seed + 4)
        ink.line(Ls_[::8], 0.026 * S, tone=0.7, seed=seed + 6 + k, taper=(0.1, 0.3), head=0.2)
        ink.line(Rs_[::8], 0.022 * S, tone=0.6, seed=seed + 8 + k, taper=(0.1, 0.3))
        sp = spline(shoe, 1.5, closed=True)
        ink.cover([sp], seed=seed + 10 + k, feather=0.7)
        ink.fill([sp], SHOE, seed=seed + 12 + k)
        ink.line(sp[::4], 0.026 * S, tone=0.85, seed=seed + 14 + k, closed=True, taper=(0.0, 0.0))
    # 长裙：A 字，下摆随步子轻摆
    sway = 0.06 * sw
    skirt = [(-0.47, 1.2), (0.31, 1.2), (0.42, 1.62), (0.50, 2.4), (0.60 + sway, 3.30), (0.30 + sway, 3.37),
             (0.0 + sway, 3.39), (-0.35 + sway, 3.38), (-0.70 + sway, 3.35), (-0.62, 2.4), (-0.54, 1.62)]
    sk = spline(T(skirt), 3.0, closed=True)
    ink.cover([sk], seed=seed + 20, feather=0.9)
    ink.fill([sk], 'skirt', seed=seed + 21)
    ink.shade([T([(-0.55, 1.6), (-0.15, 1.6), (-0.30, 3.36), (-0.70 + sway, 3.35)])], amount=0.35, seed=seed + 22,
              angle=80 if f > 0 else 100)
    ink.line(T(skirt[:5]), 0.04 * S, tone=0.8, seed=seed + 23, taper=(0.1, 0.3), head=0.3, dry=0.4, dry_from=0.6)
    ink.line(T(skirt[4:9]), 0.04 * S, tone=0.8, seed=seed + 24, taper=(0.1, 0.3), head=0.3)
    ink.line(T(skirt[8:] + [(-0.47, 1.2)]), 0.05 * S, tone=0.85, seed=seed + 25, taper=(0.1, 0.3), head=0.4,
             dry=0.5, dry_from=0.6)
    for k, (a, b) in enumerate((((-0.20, 1.75), (-0.32 + sway, 3.30)), ((0.12, 1.75), (0.20 + sway, 3.30)),
                                ((-0.45, 2.0), (-0.55 + sway, 3.28)))):
        ink.line(T([a, ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2), b]), 0.026 * S, tone=0.4, seed=seed + 30 + k,
                 role='detail', taper=(0.4, 0.3), dry=0.6, dry_from=0.3)


def _girl_legs_sit(pen, ink, R):
    """坐姿：臀在椅面上，大腿向前，小腿垂下；长裙盖住大腿垂过膝。"""
    S, f = R.S, R.f
    seed = R.seed + 330
    sy = float(R.pose.get('sit_y', R.N0[1] + 1.62 * S))
    base = R.T([(0.0, 0.0)])[0]
    hv = (sy - base[1]) / S         # 椅面相对颈根的高度（单位 s）

    def Tq(pts):
        p = np.asarray(pts, np.float32).reshape(-1, 2).copy()
        p[:, 1] += hv - 1.62
        return R.T(p)
    knee_u = 1.08
    legs = []
    for k, du in enumerate((0.06, -0.06)):
        P = Tq([(0.10 + du, 1.55), (knee_u + du, 1.60), (knee_u - 0.05 + du, 2.40), (knee_u - 0.08 + du, 3.05)])
        poly, Ls_, Rs_ = tube(P[1:], [0.16 * S, 0.12 * S, 0.095 * S])
        a = (knee_u - 0.08 + du, 3.05)
        shoe = Tq([(a[0] - 0.08, a[1] - 0.04), (a[0] + 0.05, a[1] - 0.05), (a[0] + 0.27, a[1] + 0.07),
                   (a[0] + 0.30, a[1] + 0.16), (a[0] - 0.09, a[1] + 0.17)])
        legs.append((k, poly, Ls_, Rs_, shoe))
    for k, poly, Ls_, Rs_, shoe in legs:
        ink.cover([poly], seed=seed + k, feather=0.8)
        ink.fill([poly], TIGHTS, seed=seed + 2 + k)
        ink.line(Ls_[::8], 0.024 * S, tone=0.7, seed=seed + 6 + k, taper=(0.1, 0.3))
        ink.line(Rs_[::8], 0.020 * S, tone=0.6, seed=seed + 8 + k, taper=(0.1, 0.3))
        sp = spline(shoe, 1.5, closed=True)
        ink.cover([sp], seed=seed + 10 + k, feather=0.7)
        ink.fill([sp], SHOE, seed=seed + 12 + k)
        ink.line(sp[::4], 0.024 * S, tone=0.85, seed=seed + 14 + k, closed=True, taper=(0.0, 0.0))
    skirt = [(-0.47, 1.25), (0.31, 1.25), (0.50, 1.45), (1.12, 1.46), (1.24, 1.62), (1.24, 2.15), (1.20, 2.62),
             (0.95, 2.66), (0.92, 1.86), (0.30, 1.86), (-0.58, 1.80), (-0.60, 1.55)]
    sk = spline(Tq(skirt), 3.0, closed=True)
    ink.cover([sk], seed=seed + 20, feather=0.9)
    ink.fill([sk], 'skirt', seed=seed + 21)
    ink.shade([Tq([(-0.60, 1.55), (0.6, 1.6), (0.9, 1.86), (-0.58, 1.80)])], amount=0.35, seed=seed + 22, angle=10)
    ink.line(Tq(skirt[1:7]), 0.042 * S, tone=0.82, seed=seed + 23, taper=(0.1, 0.3), head=0.3, dry=0.4,
             dry_from=0.6)
    ink.line(Tq(skirt[6:11]), 0.04 * S, tone=0.75, seed=seed + 24, taper=(0.1, 0.3))
    ink.line(Tq(skirt[10:] + [(-0.47, 1.25)]), 0.05 * S, tone=0.85, seed=seed + 25, taper=(0.1, 0.3), head=0.4)
    ink.line(Tq([(1.15, 1.70), (1.17, 2.2), (1.10, 2.6)]), 0.024 * S, tone=0.4, seed=seed + 26, role='detail',
             taper=(0.4, 0.3), dry=0.6)


def _girl_arms(pen, ink, R, which, specs):
    """which='far'（身后/身前的远侧手臂）或 'near'。"""
    S, f = R.S, R.f
    seed = R.seed + (40 if which == 'near' else 140)
    spec = specs.get(which)
    if spec is None:
        return None
    br = R.br
    if which == 'near':
        shp = R.TB([(-0.36, 0.22)])[0] + np.float32([0, 0.5 * br])
    else:
        shp = R.TB([(0.28, 0.18)])[0] + np.float32([0, 0.5 * br])
    l1, l2 = 1.10 * S, 0.96 * S
    if spec.get('hang'):
        spec = dict(spec, hand=_hang(R, shp, l1, l2, spec.get('fwd', 0.06)))
    elb, wr, hand = _arm_geom(R, shp, spec, l1, l2)
    tool = spec.get('tool')
    out = dict(hand=hand, wrist=wr, elbow=elb, shoulder=shp)
    if which == 'near' and tool and tool[0] in ('bowl', 'cup'):
        _tool_bowl(ink, R, tool[1], tool[2], seed + 70, what=tool[0])
    if tool and tool[0] == 'spoon':
        _tool_spoon(ink, R, hand, np.float32(tool[1]), seed + 30)
        out['tool_tip'] = np.float32(tool[1])
    # 袖子下侧：手臂弯向的那一侧（法向朝下的一边）
    fv = _unit(wr - elb)
    nrm = _perp(fv)
    under_side = 1 if nrm[1] > 0 else -1
    _sleeve(ink, R, shp, elb, wr, hand, spec, seed, ('sweater', 'skin'), under_side=under_side)
    thumb = spec.get('thumb', -1) * f
    _hand(ink, R, wr, hand, spec.get('shape', 'flat'), thumb=thumb, seed=seed + 50)
    return out


def girl_silhouette(pose):
    """她的大致剪影（场景坐标多边形列表），给场景做“留白”光晕用。"""
    R = _GirlRig(pose)
    out = R.silhouette()
    arm = pose.get('arm')
    if arm:
        specs = ARM_POSES[arm](pose.get('arm_t', 0.0), pose.get('arm_args', {}), R)
        sp = specs.get('near')
        if sp is not None:
            shp = R.TB([(-0.36, 0.22)])[0]
            elb, wr, hand = _arm_geom(R, shp, sp, 1.10 * R.S, 0.96 * R.S)
            poly, _, _ = tube([shp, elb, wr, hand], [0.3 * R.S, 0.25 * R.S, 0.2 * R.S, 0.15 * R.S])
            out.append(poly)
    return out


def girl(pen, pose, parts=None):
    """画她（见模块文档）。"""
    R = _GirlRig(pose)
    parts = set(parts) if parts else {'body', 'head', 'arm'}
    ink = _Ink(pen, R.S, clip=R.clip)
    arm = pose.get('arm')
    specs = ARM_POSES[arm](pose.get('arm_t', 0.0), pose.get('arm_args', {}), R) if arm else {}
    if R.back:
        return _girl_back_entry(pen, pose, R, ink, parts, specs)
    if specs.get('far') is None and R.body in ('stand', 'sit') and not R.clip.active:
        # 默认远侧手臂：自然垂在身侧（大半被身体挡住）；坐着时手搭在大腿上
        if R.body == 'stand':
            specs['far'] = dict(hang=True, fwd=0.10, shape='flat', thumb=1, front=False)
        else:
            specs['far'] = dict(hand=R.TB([(0.75, 1.42)])[0], shape='flat', thumb=1, front=False)
    if specs.get('near') is None and R.body in ('stand', 'sit') and not R.clip.active:
        if R.body == 'stand':
            specs['near'] = dict(hang=True, fwd=0.02, shape='flat', thumb=-1)
        else:
            specs['near'] = dict(hand=R.TB([(0.62, 1.45)])[0], shape='flat', thumb=-1)
    info = dict(sil=None)
    use_group = pose.get('group', True)
    ctx = pen.group(pose.get('name', 'girl'), boil=R.boil, bleed=1.1) if use_group else _nullctx()
    with ctx:
        if 'body' in parts:
            far = specs.get('far')
            if far is not None and not far.get('front', False):
                _girl_arms(pen, ink, R, 'far', specs)
            info['sil'] = _girl_body(pen, ink, R)
            if far is not None and far.get('front', False):
                _girl_arms(pen, ink, R, 'far', specs)
        if 'head' in parts or 'arm' in parts:
            # 头的几何（arm 需要眼睛位置等）
            pass
        if 'head' in parts:
            hd = _build_head(pen, R, 'girl')
            _head_paint(pen, ink, R, hd, 'girl', 'full')
            info['eye'] = tuple(None if e_ is None else e_['c'] for e_ in R.eyes)
        if 'arm' in parts:
            ink_a = ink if pose.get('clip_arms', True) else _Ink(pen, R.S, clip=None)
            a = _girl_arms(pen, ink_a, R, 'near', specs)
            if a:
                info.update(a)
    info['chin'] = R.proj(_surf(GIRL_FACE, GIRL_FACE[0][-1], 0.0)[None])[0]
    info['head_c'] = R.proj(np.float32([[0, 0, 0]]))[0]
    if 'hand' not in info and specs.get('near'):
        info['hand'] = np.float32(specs['near']['hand'])
        if specs['near'].get('tool') and specs['near']['tool'][0] == 'spoon':
            info['tool_tip'] = np.float32(specs['near']['tool'][1])
    return info


def _girl_back_entry(pen, pose, R, ink, parts, specs):
    """背影：默认两只手自然垂下（站）/ 撑在身边的草地上（坐在地上）。"""
    for nm, sg in (('near', 1), ('far', -1)):
        if specs.get(nm) is None:
            specs[nm] = dict(hang=True, shape='flat', thumb=1) if R.body == 'stand' else                 dict(hand=R.T([(0.74 * sg, 1.58)])[0], shape='flat', thumb=1, straight=True)
    info = dict(sil=None)
    use_group = pose.get('group', True)
    ctx = pen.group(pose.get('name', 'girl'), boil=R.boil, bleed=1.1) if use_group else _nullctx()
    with ctx:
        if 'body' in parts or 'arm' in parts:
            out = _girl_back(pen, ink, R, specs)
            info['sil'] = out.get('sil')
            info['hands'] = {nm: out[nm]['hand'] for nm in ('near', 'far') if nm in out}
            fist = [nm for nm in ('near', 'far') if specs.get(nm, {}).get('shape') == 'fist']
            if fist and fist[0] in out:
                info['hand'] = out[fist[0]]['hand']
            elif 'near' in out:
                info['hand'] = out['near']['hand']
        if 'head' in parts:
            hd = _build_head(pen, R, 'girl')
            _head_paint(pen, ink, R, hd, 'girl', 'full')
    info['head_c'] = R.proj(np.float32([[0, 0, 0]]))[0]
    info['neck'] = R.TB([(0.0, 0.0)])[0]
    return info


@contextmanager
def _nullctx():
    yield None


# =========================================================================== 他
BOY_POSES = ('sit_chin', 'stand', 'sit_eat')


class _BoyRig(_GirlRig):
    def __init__(self, pose):
        self.pose = pose
        self.S = S = float(pose.get('s', 126))
        self.back = bool(pose.get('back', False))
        self.f = f = 1 if (self.back or pose.get('facing', -1) >= 0) else -1
        self.ts = f
        self.tilt = float(pose.get('tilt', 0.0))
        self.seed = int(pose.get('seed', 2000))
        br = math.sin(2 * math.pi * pose.get('breath', 0.0))
        self.br = br
        self.N0 = np.float32([pose['x'], pose['y'] - 0.6 * br])
        self.lean = float(pose.get('lean', 0.0))
        self.body = {'stand': 'stand', 'ground': 'ground'}.get(pose.get('pose', 'sit_chin'), 'sit')
        self.light = float(pose.get('light', 1.0))
        self.erase = float(pose.get('erase', 0.0))
        self.face_tab = BOY_FACE
        self.face = _face_of(pose.get('face', 'smile'))
        self.face['open'] = self.face['open'] * (1.0 - float(pose.get('blink', 0.0)))
        self.hip_v = 1.6
        piv = self.TB([(0.0 if self.back else 0.10, -0.40)])[0]
        self.proj = HeadProj(piv, S, pose.get('yaw', 180 if self.back else 36), pose.get('pitch', -6),
                             pose.get('roll', 0 if self.back else 7), flip=f)
        hu = self.proj(np.float32([[0, -0.2, 0.3]]))[0] - self.proj(np.float32([[0, 0.2, 0.3]]))[0]
        self.head_up = _unit(hu)
        self.keep_face = None
        self.eyes = [None, None]
        self.clip = _Clipper(pose.get('clip_y'), pose.get('clip_poly'))

    def torso(self):
        front = [(0.24, -0.09), (0.32, -0.03), (0.50, 0.06), (0.60, 0.22), (0.62, 0.55), (0.58, 0.95),
                 (0.52, 1.30), (0.50, 1.60)]
        back = [(-0.22, -0.08), (-0.32, -0.04), (-0.58, 0.10), (-0.76, 0.26), (-0.80, 0.60), (-0.76, 1.00),
                (-0.70, 1.32), (-0.70, 1.62)]
        hem = [(-0.35, 1.66), (0.0, 1.67), (0.30, 1.64)]
        return front, back, hem


def _boy_arm_specs(R):
    S, f, T = R.S, R.f, R.TB
    p = R.pose
    kind = p.get('pose', 'sit_chin')
    if kind == 'sit_chin':
        return dict(kind='chin', elbow=np.float32(p.get('elbow', T([(0.80, 0.98)])[0])),
                    elbow2=np.float32(p.get('elbow2', T([(-0.86, 1.02)])[0])),
                    hand2=np.float32(p.get('hand2', T([(0.18, 1.14)])[0])))
    if kind == 'sit_eat':
        at = np.float32(p.get('bowl', T([(0.45, 0.95)])[0]))
        return dict(kind='hold', at=at, r=0.22 * S)
    return dict(kind='stand')


def boy(pen, pose, mode='sketch'):
    """画他（见模块文档）。sketch 与 full 用同一套几何。"""
    R = _BoyRig(pose)
    S, f = R.S, R.f
    sketch = mode == 'sketch'
    er = R.erase
    brk = 0.62 * er if sketch else 0.0
    ink = _Ink(pen, S, clip=R.clip, breaks=brk, sketch=sketch,
               role_map={'contour': 'sketch', 'detail': 'sketch', 'feature': 'sketch'} if sketch else None)
    seed = R.seed
    if sketch:
        ctx = pen.group(pose.get('name', 'boy'), boil=float(pose.get('boil', 2.1)), knock=False,
                        opacity=float(pose.get('opacity', 0.6)), bleed=0.7)
    else:
        ctx = pen.group(pose.get('name', 'boy'), boil=float(pose.get('boil', 1.0)), bleed=1.0)
    lc = 'graphite' if sketch else None
    info = {}
    spec = _boy_arm_specs(R)
    with ctx:
        # ---------------- 起形辅助线（只有草稿有）
        if sketch:
            hy, hw, hf, hb = _resample(_BY, [_BW, _BF, _BB], 16)
            G, ph = _rings(hy, hw * 1.03, hf + 0.01, hb - 0.01, 36)
            Pg = R.proj(G)
            hull = cv2.convexHull(np.round(Pg.reshape(-1, 2) * 4).astype(np.int32)).reshape(-1, 2).astype(np.float32) / 4
            hull = hull[::max(1, len(hull) // 16)]
            pen.line(hull, 0.013 * S, tone=0.36, role='construct', color='graphite', seed=seed + 1, closed=True,
                     reps=2, spread=2.8, breaks=brk * 0.7)
            mer = R.proj(np.float32([[0.0, y, np.interp(y, _BY, _BF) + 0.012] for y in np.linspace(-0.47, 0.5, 9)]))
            if not R.back:
                pen.line(mer, 0.012 * S, tone=0.34, role='construct', color='graphite', seed=seed + 2,
                         breaks=brk * 0.7)
            hwv, fr, bk = (np.interp(0.03, _BY, c) for c in (_BW, _BF, _BB))
            zc, hd_ = (fr + bk) / 2, (fr - bk) / 2
            eyl = [[hwv * math.cos(a) * 1.02, 0.03, zc + hd_ * math.sin(a)] for a in np.linspace(0.1, 0.95, 9) * math.pi]
            if not R.back:
                pen.line(R.proj(np.float32(eyl)), 0.012 * S, tone=0.34, role='construct', color='graphite',
                         seed=seed + 3, breaks=brk * 0.7)
        if sketch and not R.back:
            spine = np.vstack([R.proj(np.float32([[0.0, -0.52, -0.08], [-0.05, 0.1, -0.42]])),
                               R.TB([(-0.22, 0.1), (-0.40, 0.6), (-0.46, 1.2), (-0.36, 1.8)])])
            ink.line(spine, 0.014 * S, tone=0.36, role='construct', color='graphite', seed=seed + 4,
                     breaks=brk * 0.6)
            ink.line(R.TB([(0.62, 0.14), (0.0, 0.10), (-0.78, 0.24)]), 0.013 * S, tone=0.30, role='construct',
                     color='graphite', seed=seed + 5, breaks=brk * 0.6)
        # ---------------- 身体（毛衣 + 衬衫领）；腿（站）
        if R.back:
            ob = _boy_back(pen, ink, R, sketch)
            info['hands'] = {nm: ob[nm]['hand'] for nm in ('near', 'far')}
            info['shoulders'] = {nm: ob[nm]['shoulder'] for nm in ('near', 'far')}
        else:
            if R.body == 'stand':
                _boy_legs(pen, ink, R, sketch)
            _boy_torso(pen, ink, R, sketch)
            # 远侧手臂在身后的情况（站立时自然下垂）
            if spec['kind'] == 'stand':
                _boy_arm(pen, ink, R, 'far', None, 'flat', sketch, front=False)
        # ---------------- 头
        hd = _build_head(pen, R, 'boy')
        _head_paint(pen, ink, R, hd, 'boy', 'sketch' if sketch else 'full')
        info['chin'] = R.proj(np.float32([[0.0, 0.48, 0.24]]))[0]
        # ---------------- 手臂
        if R.back:
            pass
        elif spec['kind'] == 'chin':
            # 近侧：肘落在桌上，前臂平放
            _boy_arm(pen, ink, R, 'near', spec['hand2'], 'flat', sketch, elbow=spec['elbow2'])
            # 远侧：肘撑桌，前臂立起，手托下巴（在脸前）
            chin = info['chin']
            handc = chin + np.float32([0.02 * f * S, 0.10 * S])
            _boy_arm(pen, ink, R, 'far', handc, 'chin', sketch, elbow=spec['elbow'], front=True)
            info['hand'] = handc
        elif spec['kind'] == 'hold':
            at, r = spec['at'], spec['r']
            _boy_arm(pen, ink, R, 'far', at + np.float32([0.75 * r * f, 0.15 * r]), 'cup', sketch, front=True)
            _tool_bowl(ink, R, at, r, seed + 70, role='sketch' if sketch else 'contour', fill=not sketch)
            _boy_arm(pen, ink, R, 'near', at + np.float32([-0.55 * r * f, 0.25 * r]), 'cup', sketch)
            info['hand'] = at
        else:
            _boy_arm(pen, ink, R, 'near', None, 'flat', sketch)
        # ---------------- 被擦掉：橡皮擦痕（宽的斜向提白）+ 一点石墨蹭开的灰
        if sketch and er > 0.001:
            hc = R.proj(np.float32([[0.0, -0.05, 0.0]]))[0]
            r = rng(seed, 990)
            for k in range(4):
                c0 = hc + np.float32([r.uniform(-0.5, 0.5) * S, (k * 0.55 - 0.2) * S])
                ang = math.radians(r.uniform(-35, -15))
                v = np.float32([math.cos(ang), math.sin(ang)])
                L = (0.6 + 0.9 * er) * S * min(1.0, er * 2.2 - k * 0.25)
                if L <= 4:
                    continue
                poly, _, _ = tube([c0 - v * L / 2, c0 + v * L / 2 + np.float32([0, 0.04 * S])],
                                  [0.12 * S, 0.20 * S, 0.16 * S])
                pen.lift([poly], amt=0.85 * min(1.0, er * 1.6), seed=seed + 991 + k, soft=3.0, dry=0.6)
                pen.shade([poly], amount=0.05 * er, color='graphite', seed=seed + 995 + k, soft=6.0)
    info['head_c'] = R.proj(np.float32([[0, 0, 0]]))[0]
    return info


def _boy_torso(pen, ink, R, sketch):
    S, f, TB = R.S, R.f, R.TB
    seed = R.seed + 30
    front, back, hem = R.torso()
    sil = spline(TB([(-0.22, -0.10), (0.24, -0.11)] + front[1:] + hem[::-1] + back[::-1][:-1]), 3.0, closed=True)
    vneck = TB([(-0.34, 0.03), (-0.05, 0.45), (0.32, 0.01)])
    shirt_v = spline(TB([(-0.30, 0.0), (-0.20, -0.06), (0.0, -0.08), (0.24, -0.05), (0.30, 0.0), (-0.05, 0.42)]),
                     2.0, closed=True)
    col_l = TB([(-0.24, -0.06), (-0.07, 0.13), (0.02, -0.02)])
    col_r = TB([(0.02, -0.02), (0.15, 0.14), (0.27, -0.05)])
    shade_poly = np.vstack([TB(back[2:]), TB([(-0.50, 1.64), (-0.45, 1.0), (-0.48, 0.5), (-0.40, 0.15)])])
    if not sketch:
        ink.cover([sil], seed=seed, feather=1.0, jit=0.6)
        ink.fill([sil], 'boy_sweater', seed=seed + 1)
        ink.shade([shade_poly], amount=0.32, seed=seed + 2, angle=62 if f > 0 else 118)
        ink.cover([shirt_v], seed=seed + 3, feather=0.8)
        ink.fill([shirt_v], 'boy_shirt', seed=seed + 4)
        for k, cp in enumerate((col_l, col_r)):
            sp = spline(cp, 1.5, closed=True)
            ink.cover([sp], seed=seed + 5 + k, feather=0.7)
            ink.fill([sp], 'boy_shirt', seed=seed + 7 + k)
        ink.shade([TB([(-0.30, 0.0), (0.30, 0.0), (0.0, 0.18)])], amount=0.2, seed=seed + 9)
    else:
        ink.hatch([shade_poly], 62 if f > 0 else 118, 7, seed=seed + 39, tone=0.34 * (1 - 0.6 * R.erase),
                  color='graphite')
    lc = 'graphite' if sketch else None
    ink.line(TB(back[1:]), 0.024 * S * (1 if sketch else 2.4), tone=0.78, seed=seed + 35, color=lc, head=0.5,
             lift=0.3, dry=0.6, dry_from=0.5)
    ink.line(TB(front[1:-1]), 0.024 * S * (1 if sketch else 2.0), tone=0.72, seed=seed + 36, color=lc, head=0.4,
             dry=0.5, dry_from=0.5)
    if not sketch or R.body == 'stand':
        ink.line(TB([back[-1]] + hem + [front[-1]]), 0.024 * S * (1 if sketch else 1.6), tone=0.7, seed=seed + 38,
                 color=lc)
    ink.line(vneck, 0.022 * S * (1 if sketch else 1.4), tone=0.72, seed=seed + 34, color=lc, role='contour')
    ink.line(col_l, 0.022 * S, tone=0.78, seed=seed + 32, color=lc)
    ink.line(col_r, 0.022 * S, tone=0.78, seed=seed + 33, color=lc)
    ink.line(TB([(-0.30, 1.0), (-0.12, 1.08), (0.10, 1.05)]), 0.018 * S, tone=0.32, seed=seed + 37, color=lc,
             role='detail', dry=0.6)


def _boy_legs(pen, ink, R, sketch):
    S, T = R.S, R.T
    seed = R.seed + 300
    lc = 'graphite' if sketch else None
    for k, u0 in enumerate((0.16, -0.22)):
        P = T([(u0 * 0.8, 1.6), (u0, 3.1), (u0 + 0.02, 4.62)])
        poly, Ls_, Rs_ = tube(P, [0.34 * S, 0.24 * S, 0.19 * S])
        a = (u0 + 0.02, 4.62)
        shoe = T([(a[0] - 0.12, a[1] - 0.06), (a[0] + 0.08, a[1] - 0.07), (a[0] + 0.34, a[1] + 0.06),
                  (a[0] + 0.36, a[1] + 0.18), (a[0] - 0.12, a[1] + 0.19)])
        sp = spline(shoe, 1.5, closed=True)
        if not sketch:
            ink.cover([poly], seed=seed + k, feather=0.8)
            ink.fill([poly], 'boy_pants', seed=seed + 2 + k)
            if k == 0:
                ink.shade([poly], amount=0.25, seed=seed + 4)
            ink.cover([sp], seed=seed + 10 + k, feather=0.7)
            ink.fill([sp], BOY_SHOE, seed=seed + 12 + k)
        ink.line(Ls_[::8], 0.026 * S, tone=0.75, seed=seed + 6 + k, color=lc)
        ink.line(Rs_[::8], 0.022 * S, tone=0.65, seed=seed + 8 + k, color=lc)
        ink.line(sp[::4], 0.024 * S, tone=0.85, seed=seed + 14 + k, closed=True, color=lc, taper=(0.0, 0.0))


def _boy_arm(pen, ink, R, which, hand, shape, sketch, elbow=None, front=True):
    S, f = R.S, R.f
    seed = R.seed + (40 if which == 'near' else 140)
    shp = R.TB([(-0.62, 0.28)] if which == 'near' else [(0.44, 0.20)])[0]
    if hand is None:
        hand = _hang(R, shp, 1.15 * S, 1.0 * S, 0.06)
    hand = np.float32(hand)
    lc = 'graphite' if sketch else None
    if shape == 'chin':
        # 托腮：肘撑在桌上，前臂立起，手掌托住下巴，四指沿脸颊
        elb = np.float32(elbow)
        fa = hand - elb
        fd = _unit(fa)
        wr = hand - fd * 0.10 * S
        _sleeve_boy(ink, R, shp, elb, wr, seed, sketch)
        # 手：松松握拳，下巴搁在食指那一排指节上；拇指在朝前（脸朝向）的一侧
        fn = _perp(fd)
        if float(fn[0]) * f < 0:
            fn = -fn
        Q = lambda u, v: hand + fd * u * S + fn * v * S
        fist = [Q(-0.11, -0.080), Q(-0.02, -0.095), Q(0.07, -0.088), Q(0.115, -0.04), Q(0.12, 0.02),
                Q(0.095, 0.075), Q(0.03, 0.095), Q(-0.06, 0.085), Q(-0.11, 0.075)]
        pp = spline(np.float32(fist), 1.5, closed=True)
        if not sketch:
            ink.pen.cover([pp], seed=seed + 60, feather=0.7)
            ink.pen.fill([pp], 'skin', seed=seed + 61)
            ink.pen.shade([spline(np.float32([Q(-0.11, -0.08), Q(0.0, -0.095), Q(0.10, -0.07), Q(0.06, -0.02),
                                              Q(-0.10, -0.03)]), 1.5, closed=True)], amount=0.22, seed=seed + 62,
                          color='skin_sh')
        ink.line(np.float32(fist[:6]), 0.022 * S, tone=0.72, seed=seed + 44, color=lc, clip=False,
                 taper=(0.2, 0.3))
        ink.line(np.float32(fist[5:]), 0.020 * S, tone=0.62, seed=seed + 48, color=lc, clip=False,
                 taper=(0.3, 0.3))
        # 弯着的四指：指节之间三道短弧
        for k, vv in enumerate((-0.045, 0.0, 0.045)):
            ink.line([Q(0.115, vv + 0.004), Q(0.075, vv - 0.004), Q(0.035, vv - 0.008)], 0.012 * S, tone=0.48,
                     seed=seed + 45 + k, role='detail', color=lc, taper=(0.2, 0.5), clip=False)
        # 拇指
        ink.line([Q(-0.04, 0.085), Q(0.03, 0.105), Q(0.075, 0.085)], 0.015 * S, tone=0.55, seed=seed + 49,
                 role='detail', color=lc, taper=(0.2, 0.5), clip=False)
        return
    if elbow is not None:
        elb = np.float32(elbow)
        hv = _unit(hand - elb)
        wr = hand - hv * 0.12 * S
    else:
        dv = hand - shp
        wr_t = hand - _unit(dv) * 0.10 * S
        elb, wr = ik2(shp, wr_t, 1.15 * S, 1.0 * S, bend=1.0 if f > 0 else -1.0)
    _sleeve_boy(ink, R, shp, elb, wr, seed, sketch)
    if shape == 'flat' and elbow is not None:
        # 平放在桌上的手：几笔
        _hand(ink, R, wr, hand, 'fist', thumb=-1, seed=seed + 50, color='skin', role='sketch' if sketch else 'contour',
              fill=not sketch, size=1.05)
    else:
        _hand(ink, R, wr, hand, shape, thumb=-f, seed=seed + 50, color='skin', role='sketch' if sketch else 'contour',
              fill=not sketch, size=1.05)


def _sleeve_boy(ink, R, shp, elb, wr, seed, sketch):
    """他的袖子：上臂、前臂分两节（弯得很厉害时也不会自交出空洞），前臂画在上臂前面。"""
    S, f = R.S, R.f
    lc = 'graphite' if sketch else None
    w = 0.024 * S if sketch else 0.042 * S
    segs = (([shp, (shp + elb) / 2, elb], [0.30 * S, 0.285 * S, 0.25 * S]),
            ([elb, (elb + wr) / 2, wr], [0.25 * S, 0.225 * S, 0.20 * S]))
    for k, (path, wds) in enumerate(segs):
        poly, Ls, Rs = tube(path, wds)
        v = _unit(np.float32(path[-1]) - np.float32(path[0]))
        n = _perp(v)
        sh_side = Ls if (n[1] - 0.5 * f * n[0]) > 0 else Rs      # 朝下、背光的一侧
        lt_side = Rs if sh_side is Ls else Ls
        if not sketch:
            extra = [ell(shp[0], shp[1], 0.15 * S, 0.14 * S, n=24), ell(elb[0], elb[1], 0.125 * S, 0.12 * S, n=20)]                 if k == 0 else []
            ink.pen.cover([poly] + extra, seed=seed + 33 + 10 * k, feather=0.9)
            ink.pen.fill([poly] + extra, 'boy_sweater', seed=seed + 34 + 10 * k)
            ink.pen.shade([np.vstack([sh_side, spline(path, 2.0)[::-1]])], amount=0.3, seed=seed + 35 + 10 * k,
                          angle=math.degrees(math.atan2(v[1], v[0])))
        n_ = len(Ls)
        a_, b_ = (int(n_ * 0.06), n_ - 1) if k == 0 else (int(n_ * 0.10), n_ - 2)
        ink.line(lt_side[a_:b_:6], w, tone=0.75, seed=seed + 36 + 10 * k, color=lc, clip=False, head=0.4, dry=0.5,
                 dry_from=0.6)
        ink.line(sh_side[a_:b_:6], w * 0.9, tone=0.68, seed=seed + 38 + 10 * k, color=lc, clip=False, dry=0.4,
                 dry_from=0.6)
    # 肘：外侧一道圆弧
    v1, v2 = _unit(elb - shp), _unit(wr - elb)
    out = _unit(v1 - v2) if float(np.hypot(*(v1 - v2))) > 0.2 else _perp(v1)
    a0 = math.degrees(math.atan2(out[1], out[0]))
    ink.line(ell(elb[0], elb[1], 0.125 * S, 0.12 * S, a0 - 60, a0 + 60, 8), w * 0.9, tone=0.72, seed=seed + 41,
             color=lc, clip=False, taper=(0.3, 0.3))
    fv = v2
    nrm = _perp(fv)
    c0 = wr - fv * 0.04 * S
    ink.line([c0 + nrm * 0.10 * S, c0 + fv * 0.01 * S, c0 - nrm * 0.10 * S], 0.022 * S, tone=0.7, seed=seed + 42,
             color=lc, clip=False)


# =========================================================================== 背影（back=True）
# 背影的身体局部坐标：u 横向（+ = 画面右 = 人物自己的右侧），v 向下，单位 s，原点颈根。
_GIRL_BACK_SIDE = [(0.15, -0.10), (0.36, 0.02), (0.52, 0.09), (0.60, 0.22), (0.60, 0.36), (0.54, 0.64),
                   (0.43, 0.98), (0.47, 1.28), (0.54, 1.58)]
_BOY_BACK_SIDE = [(0.20, -0.08), (0.48, 0.02), (0.68, 0.09), (0.78, 0.22), (0.79, 0.40), (0.72, 0.80),
                  (0.64, 1.20), (0.66, 1.62)]


def _back_outline(side, hem_v, dip=0.03):
    """左右对称的上身轮廓（从颈根左侧往下 → 下摆 → 右侧往上）。"""
    L = [(-u, v) for u, v in side]
    Rr = [(u, v) for u, v in side]
    hu = side[-1][0]
    hem = [(-hu * 0.5, hem_v + dip), (0.0, hem_v + dip * 1.2), (hu * 0.5, hem_v + dip)]
    return L + hem + Rr[::-1]


def _back_torso(pen, ink, R, side, hem_v, color, seed, sketch=False, lc=None):
    S, TB = R.S, R.TB
    sil = spline(TB(_back_outline(side, hem_v)), 3.0, closed=True)
    lx = 1.0 if R.light >= 0 else -1.0
    if not sketch:
        ink.cover([sil], seed=seed, feather=1.0, jit=getattr(R, 'boil', 1.0) * 0.6)
        ink.fill([sil], color, seed=seed + 1)
        g0, g1 = TB([(-0.62 * lx, 0.7)])[0], TB([(0.15 * lx, 0.7)])[0]
        ink.shade([sil], amount=0.30, seed=seed + 2, angle=78,
                  grad=(float(g0[0]), float(g0[1]), float(g1[0]), float(g1[1]), 1.0, 0.0))
        # 背中线一道很淡的凹影
        sp = spline(TB([(0.0, 0.30), (0.015, 0.8), (0.0, 1.30)]), 2.0)
        band, _, _ = tube(sp, [0.03 * S, 0.12 * S, 0.05 * S])
        ink.shade([band], amount=0.06, seed=seed + 3, angle=90, soft=6.0)
    w = (0.024 if sketch else 0.060) * S
    for k, sg in enumerate((-1, 1)):
        pts = TB([(sg * u, v) for u, v in side[1:]])
        ink.line(pts, w, tone=0.86 if not sketch else 0.8, seed=seed + 10 + k, color=lc, taper=(0.10, 0.25),
                 head=0.5, lift=0.3, dry=0.6, dry_from=0.5, fade=0.2, streak=0.2)
    hu = side[-1][0]
    ink.line(TB([(-hu, side[-1][1]), (-hu * 0.5, hem_v + 0.03), (0.0, hem_v + 0.036), (hu * 0.5, hem_v + 0.03),
                 (hu, side[-1][1])]), w * 0.7, tone=0.7, seed=seed + 13, color=lc, taper=(0.2, 0.3), dry=0.5,
             dry_from=0.5)
    # 肩胛骨/衣褶：几笔淡线
    for k, (a, b, c) in enumerate((((-0.42, 0.35), (-0.26, 0.48), (-0.12, 0.50)),
                                   ((0.40, 0.38), (0.26, 0.50), (0.12, 0.52)),
                                   ((-0.30, 1.05), (-0.10, 1.12), (0.12, 1.10)))):
        ink.line(TB([a, b, c]), 0.026 * S, tone=0.30, seed=seed + 20 + k, role='detail', color=lc,
                 taper=(0.3, 0.5), dry=0.7, dry_from=0.2, streak=0.3)
    return sil


def _back_ground_base(pen, ink, R, color, wide, seed, lc=None, sketch=False):
    """坐在地上的背影：臀部和摊开在草地上的裙摆/裤子（腿伸向前方，被身体挡住）+ 草地上的一点投影。"""
    S, T = R.S, R.T
    base_v = 1.62
    if not sketch:
        c0 = T([(0.0, base_v + 0.04)])[0]
        sh = ell(c0[0], c0[1], wide * 1.05 * S, 0.10 * S, n=28)
        ink.shade([sh], amount=0.30, seed=seed + 9, soft=6.0, angle=10)
    pts = [(-0.50, 1.20), (-0.74, 1.40), (-wide, 1.58), (-wide * 0.9, base_v + 0.05), (-0.3, base_v + 0.07),
           (0.3, base_v + 0.07), (wide * 0.9, base_v + 0.05), (wide, 1.58), (0.74, 1.40), (0.50, 1.20)]
    poly = spline(T(pts), 3.0, closed=True)
    if not sketch:
        ink.cover([poly], seed=seed, feather=0.9)
        ink.fill([poly], color, seed=seed + 1)
        ink.shade([T([(-wide, 1.50), (-0.2, 1.50), (-0.3, base_v + 0.07), (-wide * 0.9, base_v + 0.05)])],
                  amount=0.30, seed=seed + 2, angle=15)
    w = (0.024 if sketch else 0.045) * S
    ink.line(T(pts[1:5]), w, tone=0.78, seed=seed + 3, color=lc, taper=(0.2, 0.3), head=0.3, dry=0.4, dry_from=0.6)
    ink.line(T(pts[5:9]), w, tone=0.78, seed=seed + 4, color=lc, taper=(0.2, 0.3), head=0.3, dry=0.4, dry_from=0.6)
    ink.line(T([(-0.35, 1.48), (-0.55, 1.58)]), 0.022 * S, tone=0.35, seed=seed + 5, role='detail', color=lc)
    ink.line(T([(0.35, 1.50), (0.58, 1.58)]), 0.022 * S, tone=0.35, seed=seed + 6, role='detail', color=lc)
    return poly


def _girl_back_legs(pen, ink, R):
    """站立背影：长裙 + 裙下的小腿和鞋跟。"""
    S, T = R.S, R.T
    seed = R.seed + 560
    for k, u0 in enumerate((-0.15, 0.15)):
        P = T([(u0 * 0.9, 3.0), (u0, 3.8), (u0 * 1.05, 4.47)])
        poly, Ls_, Rs_ = tube(P, [0.15 * S, 0.12 * S, 0.085 * S])
        ink.cover([poly], seed=seed + k, feather=0.8)
        ink.fill([poly], TIGHTS, seed=seed + 2 + k)
        ink.line(Ls_[::8], 0.024 * S, tone=0.7, seed=seed + 4 + k, taper=(0.1, 0.3))
        ink.line(Rs_[::8], 0.022 * S, tone=0.6, seed=seed + 6 + k, taper=(0.1, 0.3))
        uh = u0 * 1.05
        heel = spline(T([(uh - 0.085, 4.45), (uh + 0.085, 4.45), (uh + 0.095, 4.58), (uh, 4.63), (uh - 0.095, 4.58)]),
                      1.5, closed=True)
        ink.cover([heel], seed=seed + 8 + k, feather=0.7)
        ink.fill([heel], SHOE, seed=seed + 10 + k)
        ink.line(heel[::4], 0.022 * S, tone=0.85, seed=seed + 12 + k, closed=True, taper=(0.0, 0.0))
    skirt = [(-0.47, 1.20), (-0.56, 1.62), (-0.68, 2.40), (-0.80, 3.32), (-0.40, 3.38), (0.0, 3.36), (0.40, 3.39),
             (0.80, 3.32), (0.68, 2.40), (0.56, 1.62), (0.47, 1.20)]
    sk = spline(T(skirt), 3.0, closed=True)
    ink.cover([sk], seed=seed + 20, feather=0.9)
    ink.fill([sk], 'skirt', seed=seed + 21)
    g0, g1 = T([(-0.8, 2.4)])[0], T([(0.2, 2.4)])[0]
    ink.shade([sk], amount=0.32, seed=seed + 22, angle=85,
              grad=(float(g0[0]), float(g0[1]), float(g1[0]), float(g1[1]), 1.0, 0.0))
    ink.line(T(skirt[:4]), 0.05 * S, tone=0.85, seed=seed + 23, taper=(0.1, 0.3), head=0.4, dry=0.5, dry_from=0.6)
    ink.line(T(skirt[7:]), 0.045 * S, tone=0.8, seed=seed + 24, taper=(0.1, 0.3), head=0.3, dry=0.5, dry_from=0.6)
    ink.line(T(skirt[3:8]), 0.04 * S, tone=0.8, seed=seed + 25, taper=(0.1, 0.3))
    for k, (a, b) in enumerate((((-0.20, 1.75), (-0.32, 3.30)), ((0.15, 1.75), (0.25, 3.30)),
                                ((-0.45, 2.0), (-0.58, 3.28)), ((0.42, 2.1), (0.56, 3.28)))):
        ink.line(T([a, ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2), b]), 0.026 * S, tone=0.38, seed=seed + 30 + k,
                 role='detail', taper=(0.4, 0.3), dry=0.6, dry_from=0.3)


def _back_arm(pen, ink, R, nm, spec, colors, sleeve_fn, seed):
    """背影的一只手臂。nm='near' = 人物自己的右侧（画面右），'far' = 左侧。"""
    S = R.S
    sg = 1 if nm == 'near' else -1
    side = _BOY_BACK_SIDE if colors[0] == 'boy_sweater' else _GIRL_BACK_SIDE
    su = side[3][0] - 0.07
    shp = R.TB([(su * sg, 0.22)])[0]
    l1 = float(spec.get('l1', 1.02)) * S
    l2 = float(spec.get('l2', 0.94)) * S
    if spec.get('hang'):
        d = _unit(R.TB([((su + 0.12) * sg, 1.0)])[0] - R.TB([(su * sg, 0.0)])[0])
        hand = shp + d * (0.975 * (l1 + l2) + 0.10 * S)
    else:
        hand = np.float32(spec['hand'])
    dv = hand - shp
    dist = float(np.hypot(*dv)) + 1e-6
    if spec.get('straight'):
        # 手撑在身边的地上：手臂略斜向后，画面上几乎是直的（按距离缩放两节长度）
        k_ = (dist - 0.10 * S) * 1.03 / (l1 + l2)
        l1, l2 = l1 * k_, l2 * k_
    wr_t = hand - dv / dist * 0.10 * S
    elb, wr = ik2(shp, wr_t, l1, l2, bend=float(spec.get('bend', -sg)))
    fv = _unit(wr - elb)
    under_side = 1 if _perp(fv)[1] > 0 else -1
    sleeve_fn(shp, elb, wr, hand, under_side)
    sk = bool(spec.get('_sketch'))
    _hand(ink, R, wr, hand, spec.get('shape', 'flat'), thumb=int(spec.get('thumb', 1)) * sg, seed=seed + 50,
          color=colors[1], role='sketch' if sk else 'contour', fill=not sk,
          size=1.05 if colors[0] == 'boy_sweater' else 1.0)
    return dict(hand=hand, wrist=wr, elbow=elb, shoulder=shp)


def _girl_back(pen, ink, R, specs):
    """她的背影（站 / 坐在地上）。手臂在身体两侧，先画，被后背挡住一点。"""
    seed = R.seed + 500
    out = {}
    if R.body == 'stand':
        _girl_back_legs(pen, ink, R)
    elif R.body in ('ground', 'sit'):
        _back_ground_base(pen, ink, R, 'skirt', 0.98, seed + 40)

    def slv(nm):
        sd_ = seed + (40 if nm == 'near' else 140)
        return lambda shp, elb, wr, hand, us: _sleeve(ink, R, shp, elb, wr, hand, {}, sd_, ('sweater', 'skin'),
                                                       under_side=us)
    for nm in ('far', 'near'):
        sp = specs.get(nm)
        if sp is not None:
            out[nm] = _back_arm(pen, ink, R, nm, sp, ('sweater', 'skin'), slv(nm),
                                seed + (40 if nm == 'near' else 140))
    sil = _back_torso(pen, ink, R, _GIRL_BACK_SIDE, 1.58, 'sweater', seed)
    out['sil'] = [sil]
    return out


def arm_hold_line(t, args, rig=None):
    """背影（back=True）：一只手抬到胸前高度攥着红线（拳头在身体外侧一点，看得见），另一只自然垂下。
    args: side 'right'(默认，画面右边那只)/'left'；hand 拳头位置（场景坐标，可省）；tug 0..1 越攥越紧（拳头往回收一点）。
    返回的 info['hand'] 就是拳头，场景从这里往窗外画红线。"""
    sg = 1 if args.get('side', 'right') == 'right' else -1
    tug = float(args.get('tug', 0.0))
    hand = np.float32(args['hand']) if 'hand' in args else \
        rig.TB([((0.88 - 0.06 * tug) * sg, 0.62 + 0.03 * tug)])[0]
    raised = dict(hand=hand, shape='fist', thumb=1, bend=sg, l1=0.98, l2=0.80)
    if rig.body in ('ground', 'sit'):
        hang = dict(hand=rig.T([(-0.74 * sg, 1.58)])[0], shape='flat', thumb=1, straight=True)
    else:
        hang = dict(hang=True, shape='flat', thumb=1)
    return dict(near=raised, far=hang) if sg > 0 else dict(near=hang, far=raised)


def arm_bowl_rim(t, args, rig=None):
    """坐在桌前（侧面近景）：近侧的手扶着碗沿。bowl=(cx,cy) 碗口中心，r 碗口半径（场景像素）；
    u 0..1：手从桌面（rest，可省）移到碗沿。远侧手藏在身体另一侧不画。"""
    S = rig.S
    bc = np.float32(args['bowl'])
    r = float(args.get('r', 0.55 * S))
    rim = bc + np.float32([-0.78 * r * rig.f, 0.10 * r])
    rest = np.float32(args.get('rest', rim + np.float32([-0.30 * S * rig.f, 0.30 * S])))
    u = float(smooth01(args.get('u', 1.0)))
    return dict(near=dict(hand=lerp(rest, rim, u), shape='flat', thumb=-1, tool=None), far=None)


ARM_POSES.update({'hold_line': arm_hold_line, 'bowl_rim': arm_bowl_rim})


def _boy_back(pen, ink, R, sketch):
    """他的背影（站 / 坐在地上）。手臂姿态可用 pose['arm_near'] / pose['arm_far'] 覆盖（同 _back_arm 的 spec）。"""
    S = R.S
    seed = R.seed + 500
    lc = 'graphite' if sketch else None
    out = {}
    if R.body == 'stand':
        for k, u0 in enumerate((-0.22, 0.22)):
            P = R.T([(u0 * 0.8, 1.6), (u0, 3.1), (u0 * 1.02, 4.60)])
            poly, Ls_, Rs_ = tube(P, [0.34 * S, 0.24 * S, 0.19 * S])
            heel = spline(R.T([(u0 - 0.11, 4.56), (u0 + 0.11, 4.56), (u0 + 0.12, 4.72), (u0 - 0.12, 4.72)]), 1.5,
                          closed=True)
            if not sketch:
                ink.cover([poly], seed=seed + k, feather=0.8)
                ink.fill([poly], 'boy_pants', seed=seed + 2 + k)
                ink.cover([heel], seed=seed + 8 + k, feather=0.7)
                ink.fill([heel], BOY_SHOE, seed=seed + 10 + k)
            ink.line(Ls_[::8], 0.026 * S, tone=0.75, seed=seed + 4 + k, color=lc)
            ink.line(Rs_[::8], 0.022 * S, tone=0.65, seed=seed + 6 + k, color=lc)
            ink.line(heel[::4], 0.022 * S, tone=0.85, seed=seed + 12 + k, color=lc, closed=True, taper=(0.0, 0.0))
    else:
        _back_ground_base(pen, ink, R, 'boy_pants', 1.02, seed + 40, lc=lc, sketch=sketch)
    specs = {}
    for nm, sg in (('near', 1), ('far', -1)):
        sp = R.pose.get('arm_' + nm)
        if sp is None:
            sp = dict(hang=True, shape='flat', thumb=1) if R.body == 'stand' else \
                dict(hand=R.T([(0.86 * sg, 1.58)])[0], shape='flat', thumb=1, straight=True)
        specs[nm] = dict(sp, _sketch=sketch, l1=sp.get('l1', 1.06), l2=sp.get('l2', 0.98))

    def slv(nm):
        sd_ = seed + (40 if nm == 'near' else 140)
        return lambda shp, elb, wr, hand, us: _sleeve_boy(ink, R, shp, elb, wr, sd_, sketch)
    for nm in ('far', 'near'):
        out[nm] = _back_arm(pen, ink, R, nm, specs[nm], ('boy_sweater', 'skin'), slv(nm),
                            seed + (40 if nm == 'near' else 140))
    if sketch:
        ink.hatch([spline(R.TB(_back_outline(_BOY_BACK_SIDE, 1.62)), 4.0, closed=True)], 70, 7, seed=seed + 39,
                  tone=0.30 * (1 - 0.6 * R.erase), color='graphite')
    sil = _back_torso(pen, ink, R, _BOY_BACK_SIDE, 1.62, 'boy_sweater', seed, sketch=sketch, lc=lc)
    out['sil'] = [sil]
    if sketch:
        ink.line(R.TB([(0.0, -0.05), (0.03, 0.6), (0.0, 1.2), (-0.02, 1.62)]), 0.014 * S, tone=0.34,
                 role='construct', color='graphite', seed=seed + 60)
        ink.line(R.TB([(-0.80, 0.16), (0.0, 0.10), (0.80, 0.17)]), 0.013 * S, tone=0.30, role='construct',
                 color='graphite', seed=seed + 61)
    return out


def pair_sit_back(pen, pose):
    """河边：她和他并肩坐在草地上的背影（腿伸向前方，被身体挡住）。
    pose: x, y        两人中间、地面（臀底）的场景坐标
          s           她的头高（他 = 1.08 s，更高）
          lean        0..1 她把头靠到他肩上（上身往他那边歪 + 头往他那边倒）
          girl_side   -1 她在左（默认）/ +1 她在右
          gap         两人臀部间距（单位 s，默认 1.15）
          boy_mode    'full'（默认）/'sketch'；boy_opacity、boy_erase、boy_boil 给草稿用；show_boy=False 只画她
          seed, boil, breath
    返回 dict(girl=girl 的 info, boy=boy 的 info)。"""
    s = float(pose['s'])
    x, y = float(pose['x']), float(pose['y'])
    lean = clamp(float(pose.get('lean', 0.0)))
    gs = -1 if pose.get('girl_side', -1) < 0 else 1
    gap = float(pose.get('gap', 1.22))
    sb = 1.08 * s
    xg, xb = x + gs * gap / 2 * s, x - gs * gap / 2 * s
    br = float(pose.get('breath', 0.0))
    mode = pose.get('boy_mode', 'full')
    ib = None
    if pose.get('show_boy', True):
        bp = dict(x=xb, y=y - 1.62 * sb, s=sb, back=True, pose='ground', seed=int(pose.get('boy_seed', 2000)),
                  yaw=180 - gs * 6 * lean, pitch=-2, roll=-gs * 3 * lean, breath=br + 0.3,
                  boil=float(pose.get('boy_boil', 2.1 if mode == 'sketch' else pose.get('boil', 1.0))),
                  opacity=float(pose.get('boy_opacity', 0.6)), erase=float(pose.get('boy_erase', 0.0)),
                  tilt=-gs * 2.0 * lean)
        ib = boy(pen, bp, mode=mode)
    gp = dict(x=xg, y=y - 1.62 * s, s=s, back=True, body='ground', seed=int(pose.get('seed', 1000)),
              tilt=-gs * 7.5 * lean, roll=-gs * 30.0 * lean, yaw=180 + gs * 8 * lean, pitch=4 * lean,
              boil=float(pose.get('boil', 1.0)), breath=br)
    ig = girl(pen, gp)
    return dict(girl=ig, boy=ib)


# =========================================================================== 眼泪 / 碗 / 亲额头（给场景用的小工具）
def girl_tear_point(pose, pen=None, where='eye'):
    """她近侧那只眼睛下方、泪滴的起点（where='eye'：下眼睑下方一点；'end'：cry 泪痕的下端）。
    返回场景坐标；给了 pen 就按当前取景换成屏幕坐标（pen.to_screen）。场景用它控制“正在落下的一颗泪”。"""
    R = _GirlRig(pose)
    sty = GIRL_FEAT
    best = None
    for side in (-1, 1):
        p3 = _surf(R.face_tab, sty['y_in'] + 0.045, (sty['ph_in'] + 14) * side)
        _, z = R.proj(p3[None], with_z=True)
        if best is None or z[0] > best[1]:
            best = (side, float(z[0]))
    side = best[0]
    if where == 'end':
        k = float(_face_of(pose.get('face')).get('tear', 1.0))
        p3 = _surf(R.face_tab, sty['y_in'] + 0.05 + 0.24 * max(k, 0.3), (sty['ph_in'] + 19) * side, dz=0.006)
    else:
        ph = (sty['ph_in'] + sty['ph_out']) / 2 * side
        p3 = _surf(R.face_tab, (sty['y_in'] + sty['y_out']) / 2 + 0.065, ph, dz=0.01)
    p = R.proj(p3[None])[0]
    return pen.to_screen(p[None])[0] if pen is not None else p


def tear_drop(pen, x, y, size, seed=0, stretch=0.0, boil=None):
    """一颗正在落下的泪滴（上尖下圆）：(x,y) 圆肚中心，size ≈ 圆肚半径（场景像素）；stretch 0..1 下落时拉长。"""
    r = float(size)
    k = 1.0 + 0.6 * clamp(stretch)
    top = np.float32([[x, y - r * 2.1 * k]])
    poly = spline(np.vstack([top, ell(x, y, r, r * (1.0 + 0.1 * stretch), -25, 205, 16)]), 1.0, closed=True)
    with pen.group('tear', boil=0.3 if boil is None else boil):
        pen.cover([poly], seed=(seed, 1), feather=0.6, amount=0.55)
        pen.fill([poly], 'tear', seed=(seed, 2))
        pen.line(poly, max(1.2, 0.20 * r), tone=0.62, color='water_d', seed=(seed, 3), closed=True, role='detail',
                 taper=(0.0, 0.0))
        pen.lift(ell(x - 0.35 * r, y - 0.25 * r, 0.28 * r, 0.36 * r, n=10), amt=0.9, seed=(seed, 4), soft=0.5)


class _BowlRig:
    def __init__(self, S):
        self.S = S


def bowl(pen, c, r, seed=0, role='contour'):
    """一只盛着红豆汤的碗（和他捧着的碗同一画法）：c 碗口中心，r 碗口半径（场景像素）。"""
    S = r / 0.22
    with pen.group('bowl', boil=0.6):
        _tool_bowl(_Ink(pen, S), _BowlRig(S), c, r, seed, role=role, fill=True)


def girl_forehead_point(pose):
    """（第 7 镜预留）她额头正中（刘海表面）的场景坐标：他低头亲额头时让他的嘴对到这里。"""
    R = _GirlRig(pose)
    return R.proj(np.float32([[0.0, -0.20, 0.47]]))[0]


def boy_mouth_point(pose):
    """（第 7 镜预留）他嘴的场景坐标。"""
    R = _BoyRig(pose)
    return R.proj(_surf(BOY_FACE, BOY_FEAT['mouth_y'], 0.0, dz=0.01)[None])[0]



# =========================================================================== 追加（cast3）：第 3/4/6/7/8/15 镜的新姿势
# 只追加，不改上面任何函数的行为。新接口（详见各函数说明）：
#   表情   EXPR 新增 'eat'（被喂时眯眼张嘴）'resolve'（含泪但眼神坚定）'peace'（安心地闭眼）'blow'（嘟嘴吹凉）
#          'distant'（他望向窗外，出神）
#   她     ARM_POSES 新增 'ladle'（盛汤）'push'（推碗）'place'（摆勺子）'catch'（手接在下巴下）
#          'fist_chest'（攥着红豆的拳头按在胸口）'back_table'（背影/过肩：两前臂放在桌上）
#          girl_arms(pen, pose, which)    只画手臂（支持新道具：汤勺 ladle、瓷勺 soupspoon、拳里的红豆 bean）
#          girl_with(pen, pose, props)    身体+头 → props(pen) 场景画碗/锅 → 手臂（手压在碗上）
#          girl_front(pen, pose, parts)   正面（yaw 0–35）上半身：对称的身体、两侧肩膀（第 15 镜）
#          girl_mouth_point(pose)         她嘴的场景坐标（喂汤对位）
#   他     boy_act(pen, pose, mode)       act='reach' 坐着伸手够勺子 / 'feed' 坐着喂她 / 'rise' 从椅子上站起 /
#                                         'walk' 走路（侧面或背面 back=True）/ 'door' 背对镜头开门 / 'stand'
#          dust 参数：草稿从指尖（或任意一点）开始化成灰散掉
#   两人   couple(pen, pose)              窗边：他低头亲她额头（k）→ 她靠在他胸口（hug）→ 他转头望窗外（look_away）
#                                         → 手臂松开（loosen）
EXPR.update({
    # 被喂：笑眼（∩）眯着，嘴微张，脸红
    'eat':      _E(open=0.0, gy=0.10, smile=0.42, brow=-0.05, brow_y=0.15, happy=1.0, mouth_open=0.40, blush=0.85),
    # 含泪但眼神坚定：眼里满是泪光（wet），下眼睑微微绷紧，眉头微蹙、整条眉压低一点，嘴唇抿着
    'resolve':  _E(open=0.80, gx=0.0, gy=0.02, smile=-0.12, brow=0.40, brow_out=0.05, brow_y=-0.40, happy=0.20,
                   blush=0.45, wet=1.0, tear=0.10),
    # 安心地闭眼（被亲额头、靠在他胸口）：‿ 形闭眼，嘴角浅浅上扬
    'peace':    _E(open=0.0, gy=0.30, smile=0.34, brow=0.08, brow_out=0.35, happy=0.0, blush=0.85),
    # 嘟嘴吹凉一勺汤：半垂眼看着勺子
    'blow':     _E(open=0.50, gx=0.20, gy=0.80, smile=0.05, brow=0.05, pucker=0.85, blush=0.45),
    # 出神地望向窗外
    'distant':  _E(open=0.64, gx=0.0, gy=-0.15, smile=0.0, brow=0.30, brow_out=0.25, blush=0.30, wet=0.3),
})


def girl_mouth_point(pose):
    """她嘴的场景坐标（喂汤时勺子对到这里）。"""
    R = _GirlRig(pose)
    return R.proj(_surf(GIRL_FACE, GIRL_FEAT['mouth_y'], 0.0, dz=0.01)[None])[0]


# --------------------------------------------------------------------------- 道具（握在手里的）
def _tool_ladle(ink, R, hand, tip, pour, target, seed, role='contour', fill=True):
    """长柄木汤勺：tip = 勺斗中心；pour 0..1 往前倾倒（勺斗朝人物前方倾斜，红豆汤从前沿流进 target）。"""
    pen = ink.pen
    S, f = R.S, R.f
    hv = _unit(np.float32(hand) - np.float32(tip))
    r = 0.15 * S
    pour = float(clamp(pour))
    rot = -f * 38.0 * pour                              # 勺斗往前倾
    ca, sa = math.cos(math.radians(rot)), math.sin(math.radians(rot))

    def Rt(P):
        P = np.asarray(P, np.float32) - tip
        return np.stack([P[:, 0] * ca - P[:, 1] * sa, P[:, 0] * sa + P[:, 1] * ca], 1) + tip
    cx, cy = float(tip[0]), float(tip[1])
    ry = r * 0.36
    rim = Rt(ell(cx, cy, r, ry, 0, 360, 28))
    body = Rt(np.vstack([ell(cx, cy, r, ry, 180, 360, 14), ell(cx, cy + 0.02 * S, r * 0.98, r * 0.80, 0, 180, 16)]))
    top = np.float32(hand) + hv * 0.26 * S
    c0 = np.float32(tip) + hv * r * 0.85
    hp, hl, hr = tube([c0, (c0 + np.float32(hand)) / 2, top], [0.028 * S, 0.032 * S, 0.040 * S])
    lc = 'graphite' if role == 'sketch' else None
    if fill:
        pen.cover([hp, body], seed=seed, feather=0.6)
        pen.fill([hp, body], 'wood', seed=seed + 1)
        pen.shade([Rt(ell(cx, cy + 0.30 * r, r * 0.9, r * 0.55, 0, 180, 14))], amount=0.30, seed=seed + 2)
        lvl = 1.0 - 0.75 * pour
        if lvl > 0.05:
            soup_e = Rt(ell(cx + f * 0.25 * r * pour, cy + 0.02 * r, r * 0.80 * (0.5 + 0.5 * lvl), ry * 0.70, 0, 360,
                            20))
            pen.fill([soup_e], 'soup', seed=seed + 3)
            pen.dot(cx - 0.25 * r, cy, 0.022 * S, 0.016 * S, 'bean', seed=seed + 4, rot=20)
    ink.line(rim, 0.016 * S, tone=0.8, seed=seed + 5, role=role, color=lc, closed=True, clip=False,
             taper=(0.0, 0.0))
    ink.line(body[14:], 0.020 * S, tone=0.82, seed=seed + 6, role=role, color=lc, clip=False, head=0.3)
    ink.line(hl[::6], 0.015 * S, tone=0.75, seed=seed + 7, role=role, color=lc, clip=False, taper=(0.1, 0.2),
             head=0.3, dry=0.4, dry_from=0.6)
    ink.line(hr[::6], 0.011 * S, tone=0.5, seed=seed + 8, role=role, color=lc, clip=False, taper=(0.1, 0.2))
    if pour > 0.12 and target is not None and fill:
        # 一道往下落的红豆汤：从勺斗前沿到碗里的汤面，越往下越细；中途两颗小汤滴
        lip = Rt(np.float32([[cx + f * r * 0.95, cy + 0.1 * ry]]))[0]
        tg = np.float32(target)
        k = float(smooth01((pour - 0.12) / 0.35))
        mid = lip + np.float32([f * 0.05 * S, 0.0]) + (tg - lip) * np.float32([0.25, 0.45])
        end = lip + (tg - lip) * k
        P = bez(lip, mid, end, 12)
        pen.line(P, 0.050 * S * (0.4 + 0.6 * k), tone=0.95, color='soup', seed=seed + 9, role='detail',
                 taper=(0.02, 0.55), head=0.4)
        for j in range(2):
            u = 0.55 + 0.25 * j
            q = P[min(len(P) - 1, int(u * (len(P) - 1)))] + np.float32([f * (0.02 + 0.015 * j) * S, 0.0])
            pen.dot(q[0], q[1], 0.010 * S, 0.014 * S, 'soup', seed=seed + 10 + j)


def _tool_soupspoon(ink, R, hand, tip, seed, soup=1.0, role='contour', fill=True):
    """金属汤勺（第 5 镜/T1 那一把）：tip = 勺头中心，柄从勺头穿过拳头；soup 0..1 勺里有一勺红豆汤。"""
    pen = ink.pen
    S = R.S
    hand = np.float32(hand)
    tip = np.float32(tip)
    dv = _unit(hand - tip)
    nv = np.float32([dv[1], -dv[0]])
    sl, sw = 0.13 * S, 0.055 * S
    rot = math.degrees(math.atan2(dv[1], dv[0]))
    lc = 'graphite' if role == 'sketch' else None
    handle, Lh, Rh = tube([tip + dv * (sl - 0.02 * S), (tip + hand) / 2, hand + dv * 0.09 * S],
                          [0.030 * S, 0.034 * S, 0.042 * S])
    bowl_s = ell(tip[0], tip[1], sl, sw, 0, 360, 26, rot=rot)
    if fill:
        pen.cover([handle, bowl_s], seed=seed, feather=0.6)
        pen.fill([handle, bowl_s], 'metal', seed=seed + 1)
        if soup > 0.05:
            inner = ell(tip[0] - dv[0] * 0.01 * S + nv[0] * 0.004 * S, tip[1] - dv[1] * 0.01 * S + nv[1] * 0.004 * S,
                        sl * 0.78, sw * 0.68, 0, 360, 22, rot=rot)
            pen.fill([inner], 'soup', seed=seed + 2)
            for k, (a, b) in enumerate(((-0.35, 0.05), (0.12, -0.10), (0.42, 0.12))):
                bx = tip + dv * (a * sl) + nv * (b * sw * 1.6)
                pen.dot(bx[0], bx[1], 0.023 * S, 0.016 * S, color='bean', tone=1.0, seed=(seed + 3, k),
                        rot=rot + 20 * k)
        pen.lift(ell(tip[0] - dv[0] * 0.05 * S + nv[0] * 0.025 * S, tip[1] - dv[1] * 0.05 * S + nv[1] * 0.025 * S,
                     0.025 * S, 0.011 * S, n=10, rot=rot), amt=0.7, seed=seed + 4, soft=0.8)
    ink.line(bowl_s, 0.012 * S, tone=0.8, seed=seed + 5, role=role, color=lc, closed=True, clip=False,
             taper=(0.0, 0.0))
    ink.line(Lh[::5], 0.011 * S, tone=0.75, seed=seed + 6, role=role, color=lc, clip=False, taper=(0.1, 0.2))
    ink.line(Rh[::5], 0.009 * S, tone=0.5, seed=seed + 7, role=role, color=lc, clip=False, taper=(0.1, 0.2))


def _bean_in_hand(pen, R, wrist, hand, shape, thumb, seed, size=1.0):
    """攥在手里的那颗红豆：张开（cup）时躺在掌心；握拳（fist）时只在拇指和食指的缝里露出一点红。"""
    S = R.S * size
    w = np.float32(wrist)
    d = _unit(np.float32(hand) - w)
    n = _perp(d) * thumb
    with pen.group('bean_fist', boil=0.3):
        if shape == 'fist':
            c = w + d * 0.168 * S + n * 0.052 * S
            pen.dot(c[0], c[1], 0.030 * S, 0.020 * S, 'bean', seed=seed, rot=math.degrees(math.atan2(d[1], d[0])))
            pen.lift(ell(c[0] - 0.006 * S, c[1] - 0.005 * S, 0.006 * S, 0.004 * S, n=8), amt=0.6, seed=seed + 1,
                     soft=0.4)
            # 指缝的一笔压在豆子上（豆子被攥住）
            pen.line([w + d * 0.13 * S + n * 0.045 * S, w + d * 0.19 * S + n * 0.040 * S], 0.012 * S, tone=0.55,
                     seed=seed + 2, role='detail', taper=(0.3, 0.3))
        else:
            c = w + d * 0.14 * S - n * 0.005 * S
            pen.dot(c[0], c[1], 0.034 * S, 0.026 * S, 'bean', seed=seed, rot=30)
            pen.line(ell(c[0], c[1], 0.034 * S, 0.026 * S, 200, 330, 8, rot=30), 0.008 * S, tone=0.8, color='bean_d',
                     seed=seed + 3, role='detail', taper=(0.2, 0.2))
            pen.lift(ell(c[0] - 0.010 * S, c[1] - 0.008 * S, 0.009 * S, 0.006 * S, n=8), amt=0.7, seed=seed + 1,
                     soft=0.4)


def _xtool_pre(pen, ink, R, spec, hand, seed):
    tool = spec.get('tool')
    if not tool:
        return
    sk = getattr(ink, 'sketch', False)
    role = 'sketch' if sk else 'contour'
    if tool[0] in ('bowl', 'cup'):
        _tool_bowl(ink, R, tool[1], tool[2], seed + 70, what=tool[0], role=role, fill=not sk)
    elif tool[0] == 'spoon':
        _tool_spoon(ink, R, hand, np.float32(tool[1]), seed + 30, role=role, fill=not sk)
    elif tool[0] == 'ladle':
        _tool_ladle(ink, R, hand, np.float32(tool[1]), tool[2], tool[3], seed + 30, role=role, fill=not sk)
    elif tool[0] == 'soupspoon':
        _tool_soupspoon(ink, R, hand, np.float32(tool[1]), seed + 30, soup=tool[2] if len(tool) > 2 else 1.0,
                        role=role, fill=not sk)


def _girl_arm_at(pen, ink, R, shp, spec, seed, l1=1.10, l2=0.96):
    """她的一只手臂，肩在 shp（任意位置；_girl_arms 的一般化），支持新道具。返回 hand/wrist/elbow/shoulder。"""
    S, f = R.S, R.f
    l1, l2 = l1 * S, l2 * S
    if spec.get('hang'):
        spec = dict(spec, hand=_hang(R, shp, l1, l2, spec.get('fwd', 0.06)))
    elb, wr, hand = _arm_geom(R, shp, spec, l1, l2)
    out = dict(hand=hand, wrist=wr, elbow=elb, shoulder=shp)
    tool = spec.get('tool')
    _xtool_pre(pen, ink, R, spec, hand, seed)
    if tool and tool[0] in ('spoon', 'soupspoon', 'ladle'):
        out['tool_tip'] = np.float32(tool[1])
    fv = _unit(wr - elb)
    under_side = 1 if _perp(fv)[1] > 0 else -1
    _sleeve(ink, R, shp, elb, wr, hand, spec, seed, ('sweater', 'skin'), under_side=under_side)
    thumb = spec.get('thumb', -1) * f
    shape = spec.get('shape', 'flat')
    _hand(ink, R, wr, hand, shape, thumb=thumb, seed=seed + 50)
    if tool and tool[0] == 'bean':
        _bean_in_hand(pen, R, wr, hand, shape, thumb, seed + 90)
    return out


def _girl_shoulders(R):
    br = np.float32([0, 0.5 * R.br])
    return dict(near=R.TB([(-0.36, 0.22)])[0] + br, far=R.TB([(0.28, 0.18)])[0] + br)


def girl_arms(pen, pose, which=('far', 'near'), group=True):
    """只画她的手臂（pose['arm'] 的姿态），和 girl() 用同一套几何，另外支持新道具：
    tool=('ladle', 勺斗中心, pour, 汤落点) 长柄木汤勺 / ('soupspoon', 勺头中心, 汤量) 金属汤勺 / ('bean',) 拳里的红豆。
    which：画哪几只（按顺序，'far' 先画在后面）。clip_arms 同 girl()。返回 {which: dict(hand, wrist, elbow, shoulder,
    tool_tip?)}。用法见 girl_with()。"""
    R = _GirlRig(pose)
    arm = pose.get('arm')
    if not arm:
        return {}
    specs = ARM_POSES[arm](pose.get('arm_t', 0.0), pose.get('arm_args', {}), R)
    ink = _Ink(pen, R.S, clip=R.clip if pose.get('clip_arms', True) else None)
    shs = _girl_shoulders(R)
    out = {}
    ctx = pen.group(pose.get('name', 'girl') + '_arms', boil=R.boil, bleed=1.1) if group else _nullctx()
    with ctx:
        for w in which:
            sp = specs.get(w)
            if sp is None:
                continue
            out[w] = _girl_arm_at(pen, ink, R, shs[w], sp, R.seed + (40 if w == 'near' else 140))
            for k in ('bowl_at', 'pour'):
                if k in sp:
                    out[w][k] = sp[k]
    return out


def girl_with(pen, pose, props=None):
    """她：身体 + 头 → props(pen)（场景在这里画桌上的锅、碗：在她身前、被她的手压着）→ 两只手臂（含道具）。
    第 3 镜盛汤 / 推碗都用它。返回 dict(head=girl() 的 info, arms=girl_arms 的返回)。"""
    info = girl(pen, dict(pose, arm=None), parts=('body', 'head'))
    if props is not None:
        props(pen)
    arms = girl_arms(pen, pose)
    return dict(head=info, arms=arms)


# --------------------------------------------------------------------------- 她的新手臂姿态
def arm_ladle(t, args, rig=None):
    """第 3 镜·站在桌边盛汤：近侧手（她的右手）握长柄木汤勺从锅里舀汤倒进小碗，远侧手扶着小碗。
    args: pot=(cx,cy) 锅里汤面中心；bowl=(cx,cy) 小碗碗口中心；r 碗口半径（默认 0.42 s）；
          u 0..1 一勺的进度：0–0.28 在锅里舀 → 0.28–0.55 端过去 → 0.55–0.90 倾倒（pour 先升后落）→ 0.90–1 收回。
          steady=False 远侧手不扶碗（垂在身侧被挡住）。
    near['tool'] = ('ladle', 勺斗中心, pour, 汤落点)，near['pour'] 当前倾倒量。"""
    S, f = rig.S, rig.f
    pot = np.float32(args['pot'])
    bw = np.float32(args['bowl'])
    r = float(args.get('r', 0.42 * S))
    u = float(clamp(args.get('u', 0.0)))
    above = bw + np.float32([-0.45 * r * f, -0.40 * S])
    exit_ = pot + np.float32([0.10 * S * f, -0.10 * S])
    pour = 0.0
    if u < 0.28:
        q = float(smooth01(u / 0.28))
        tip = pot + np.float32([(-0.12 + 0.22 * q) * S * f, 0.035 * S * math.sin(math.pi * q) - 0.01 * S])
    elif u < 0.55:
        q = float(smooth01((u - 0.28) / 0.27))
        tip = lerp(exit_, above, q) + np.float32([0, -0.20 * S * math.sin(math.pi * q)])
    elif u < 0.90:
        q = (u - 0.55) / 0.35
        pour = float(smooth01(q / 0.30) * (1.0 - smooth01((q - 0.72) / 0.28)))
        tip = above + np.float32([0.04 * S * f, 0.03 * S]) * pour
    else:
        q = float(smooth01((u - 0.90) / 0.10))
        tip = above + np.float32([-0.10 * S * f, -0.06 * S]) * q
    tip = np.float32(tip)
    off = np.float32([-0.62 * S * f, -0.36 * S])
    a = math.radians(-f * 22.0 * pour)
    off = np.float32([off[0] * math.cos(a) - off[1] * math.sin(a), off[0] * math.sin(a) + off[1] * math.cos(a)])
    hand = tip + off
    tgt = bw + np.float32([0.0, 0.06 * r])
    near = dict(hand=hand, shape='fist', thumb=-1, tool=('ladle', tip, pour, tgt), pour=pour)
    far = None
    if args.get('steady', True):
        far = dict(hand=bw + np.float32([-1.02 * r * f, 0.22 * r]), shape='cup', thumb=1, front=True,
                   bend=float(args.get('far_bend', -f)))
    return dict(near=near, far=far)


def arm_push(t, args, rig=None):
    """第 3 镜·把一只碗往前推：近侧手的手指搭在碗沿后侧，手掌推着碗往前滑。
    args: bowl=(cx,cy) 碗口中心起点；to=(cx,cy) 终点；r 碗口半径；u 0..1（缓入缓出）。
    碗当前位置 = lerp(bowl, to, smooth01(u))（near['bowl_at']，girl_arms 返回里也有）；场景先画碗，再画手臂。"""
    S, f = rig.S, rig.f
    b0 = np.float32(args['bowl'])
    b1 = np.float32(args.get('to', b0 + np.float32([0.8 * S * f, -0.1 * S])))
    r = float(args.get('r', 0.42 * S))
    u = float(smooth01(args.get('u', 1.0)))
    pos = lerp(b0, b1, u)
    tipp = pos + np.float32([-0.55 * r * f, -0.02 * r])            # 指尖搭在碗沿上
    hand = tipp - np.float32([0.17 * S * f, 0.015 * S])
    return dict(near=dict(hand=hand, shape='flat', thumb=-1, bowl_at=pos), far=None)


def arm_place(t, args, rig=None):
    """第 3 镜·摆勺子：近侧手捏着金属汤勺，把它从 spoon 移到 to（碗边），u 0..1，中途抬起 lift（默认 0.15 s）。
    soup 勺里有没有汤（默认 0）。"""
    S, f = rig.S, rig.f
    a = np.float32(args['spoon'])
    b = np.float32(args.get('to', a))
    u = float(smooth01(args.get('u', 1.0)))
    tip = lerp(a, b, u) + np.float32([0, -float(args.get('lift', 0.15)) * S * math.sin(math.pi * u)])
    hand = tip + np.float32([-0.58 * S * f, -0.16 * S])
    return dict(near=dict(hand=hand, shape='fist', thumb=-1, tool=('soupspoon', tip, float(args.get('soup', 0.0)))),
                far=None)


def arm_catch(t, args, rig=None):
    """被喂汤时：近侧手掌心朝上接在下巴下面（怕汤滴下来），u 0..1 抬手进度。chin 可省（按头算）。"""
    S, f = rig.S, rig.f
    if 'chin' in args:
        chin = np.float32(args['chin'])
    else:
        chin = rig.proj(_surf(GIRL_FACE, GIRL_FACE[0][-1], 0.0)[None])[0]
    u = float(smooth01(args.get('u', 1.0)))
    rest = np.float32(args.get('rest', rig.TB([(0.55, 1.30)])[0]))
    tgt = chin + np.float32([0.16 * S * f, 0.40 * S])
    hand = lerp(rest, tgt, u)
    shp = rig.TB([(-0.36, 0.22)])[0]
    bend = _ik_low(shp, hand - _unit(hand - shp) * 0.10 * S, 1.10 * S, 0.96 * S)
    return dict(near=dict(hand=hand, shape='cup', thumb=1, bend=bend), far=None)


def arm_fist_chest(t, args, rig=None):
    """第 15 镜·攥着红豆的手按在胸口。args:
      u 0..1 抬手进度（rest → 胸口）；grip 0..1（<0.5 摊开的掌心里躺着那颗红豆，≥0.5 攥成拳，指缝露出一点红）；
      press 0..1 攥紧往胸口按（拳头往里收一点）；rest 掌心的起点（默认在身前桌面上方）；chest 胸口点（可省）；
      bean=False 不画红豆。适用于 girl()（3/4 侧）和 girl_front()（正面）。"""
    S, f = rig.S, rig.f
    u = float(smooth01(args.get('u', 1.0)))
    grip = float(clamp(args.get('grip', 1.0)))
    press = float(clamp(args.get('press', 0.0)))
    front = getattr(rig, 'front_view', False)
    rest = np.float32(args.get('rest', rig.TB([(0.10, 1.12)] if front else [(0.45, 1.20)])[0]))
    chest = np.float32(args.get('chest', rig.TB([(0.02, 0.52)] if front else [(0.12, 0.50)])[0]))
    chest = chest + np.float32([0.0, 0.02 * S * press])
    hand = lerp(rest, chest, u)
    shape = 'fist' if grip >= 0.5 else 'cup'
    tool = ('bean',) if args.get('bean', True) else None
    return dict(near=dict(hand=hand, shape=shape, thumb=1, bend=float(args.get('bend', f)), tool=tool), far=None)


def arm_back_table(t, args, rig=None):
    """背影/过肩（back=True, body='sit'）：两只前臂往前搁在桌上（手在身体前面，被背挡住，只露出上臂和肘）。
    args: spread 两肘外张（默认 1.0）；near_hand / far_hand 覆盖手的位置。"""
    sp = float(args.get('spread', 1.0))
    near = dict(hand=np.float32(args.get('near_hand', rig.TB([(0.36 + 0.08 * sp, 1.12)])[0])), shape='flat', thumb=1,
                l1=0.92, l2=0.34)
    far = dict(hand=np.float32(args.get('far_hand', rig.TB([(-0.36 - 0.08 * sp, 1.12)])[0])), shape='flat', thumb=1,
               l1=0.92, l2=0.34)
    return dict(near=near, far=far)


ARM_POSES.update({'ladle': arm_ladle, 'push': arm_push, 'place': arm_place, 'catch': arm_catch,
                  'fist_chest': arm_fist_chest, 'back_table': arm_back_table})


# --------------------------------------------------------------------------- 她 · 正面上半身
def girl_front(pen, pose, parts=None):
    """她正面（大致朝镜头，yaw 0–35）的上半身，第 15 镜夜景近景用。同一个头、同一件高领毛衣，身体是左右对称的
    正面轮廓（3/4 侧的 girl() 身体在 yaw<30 时会显得歪）。pose 同 girl()（x, y, s, facing, yaw, pitch, roll, face,
    blink, breath, light, clip_y/clip_poly, clip_arms, seed, boil），另外：
      arm         ARM_POSES 的姿态（'fist_chest' 最合适；坐标同样用 rig.TB）；不写 = 两手自然垂下（被桌面挡住）
      body_yaw    身体转向（度，默认 0.5×yaw）：领口/衣褶往转向一侧挪一点
    近侧手臂 = 画面左边那只（facing=1 时她的右手）。手在身体前面（front=True 或 fist_chest）时画在身体之后，
    否则先画、被身体挡住内侧。parts 同 girl()。返回 info：hand、chin、head_c、eye、sil。"""
    p = dict(pose)
    p['back'] = False
    R = _GirlRig(p)
    R.front_view = True
    S, f = R.S, R.f
    parts = set(parts) if parts else {'body', 'head', 'arm'}
    ink = _Ink(pen, S, clip=R.clip)
    ink_a = ink if p.get('clip_arms', True) else _Ink(pen, S, clip=None)
    arm = p.get('arm')
    specs = ARM_POSES[arm](p.get('arm_t', 0.0), p.get('arm_args', {}), R) if arm else {}
    for nm in ('near', 'far'):
        if specs.get(nm) is None:
            specs[nm] = dict(hang=True, fwd=0.0, shape='flat', thumb=1, behind=True)
        elif arm == 'fist_chest' and nm == 'near':
            specs[nm] = dict(specs[nm], front=True)
    by = float(p.get('body_yaw', 0.5 * float(p.get('yaw', 20.0))))
    shx = 0.28 * math.sin(math.radians(by))
    br = np.float32([0, 0.5 * R.br])
    shs = dict(near=R.TB([(-0.48, 0.21)])[0] + br, far=R.TB([(0.48, 0.21)])[0] + br)
    seed = R.seed
    info = dict(sil=None)

    def arm_(nm):
        sp = dict(specs[nm])
        ik_ = ink_a if sp.get('front', False) else ink
        if sp.get('hang'):
            sg = -1 if nm == 'near' else 1
            d = _unit(R.TB([(sg * 0.60, 1.0)])[0] - R.TB([(sg * 0.48, 0.0)])[0])
            sp['hand'] = shs[nm] + d * (0.975 * (2.06 * S) + 0.10 * S)
            sp.pop('hang')
        sp.setdefault('bend', -1.0 if nm == 'near' else 1.0)
        return _girl_arm_at(pen, ik_, R, shs[nm], sp, seed + (40 if nm == 'near' else 140))

    ctx = pen.group(p.get('name', 'girl'), boil=R.boil, bleed=1.1) if p.get('group', True) else _nullctx()
    with ctx:
        if 'body' in parts:
            for nm in ('far', 'near'):
                if not specs[nm].get('front', False):
                    a = arm_(nm)
                    if nm == 'near':
                        info.update(a)
            side = _GIRL_BACK_SIDE
            outline = _back_outline(side, 1.58)
            sil = spline(R.TB(outline), 3.0, closed=True)
            ink.cover([sil], seed=seed + 1, feather=1.0, jit=R.boil * 0.6)
            ink.fill([sil], 'sweater', seed=seed + 2)
            lx = 1.0 if R.light >= 0 else -1.0
            g0, g1 = R.TB([(-0.62 * lx, 0.7)])[0], R.TB([(0.20 * lx, 0.7)])[0]
            ink.shade([sil], amount=0.34, seed=seed + 3, angle=72,
                      grad=(float(g0[0]), float(g0[1]), float(g1[0]), float(g1[1]), 1.0, 0.0))
            # 胸下一点影（毛衣在胸下收进去）
            band, _, _ = tube(spline(R.TB([(-0.42 + shx, 0.70), (shx, 0.76), (0.40 + shx, 0.70)]), 2.0),
                              [0.04 * S, 0.10 * S, 0.04 * S])
            ink.shade([band], amount=0.10, seed=seed + 4, angle=0, soft=5.0)
            w = 0.060 * S
            for k, sg in enumerate((-1, 1)):
                pts = R.TB([(sg * u_, v_) for u_, v_ in side[1:]])
                ink.line(pts, w if sg * lx < 0 else w * 0.8, tone=0.86 if sg * lx < 0 else 0.72, seed=seed + 10 + k,
                         taper=(0.10, 0.25), head=0.5, lift=0.3, dry=0.6, dry_from=0.5, fade=0.2, streak=0.2)
            hu = side[-1][0]
            ink.line(R.TB([(-hu, side[-1][1]), (-hu * 0.5, 1.61), (0.0, 1.616), (hu * 0.5, 1.61), (hu, side[-1][1])]),
                     w * 0.7, tone=0.7, seed=seed + 13, taper=(0.2, 0.3), dry=0.5, dry_from=0.5)
            # 衣褶：腋下两道、胸下一道、腰间一道（跟着身体转向挪一点）
            for k, P in enumerate((((-0.50, 0.42), (-0.36, 0.55), (-0.30, 0.72)),
                                   ((0.50, 0.42), (0.38, 0.56), (0.32, 0.74)),
                                   ((-0.24 + shx, 0.80), (shx, 0.86), (0.22 + shx, 0.81)),
                                   ((-0.30 + shx, 1.18), (-0.08 + shx, 1.24), (0.16 + shx, 1.20)))):
                ink.line(R.TB(list(P)), 0.026 * S, tone=0.30, seed=seed + 20 + k, role='detail',
                         taper=(0.3, 0.5), dry=0.7, dry_from=0.2, streak=0.3)
            info['sil'] = [sil]
        if 'head' in parts:
            hd = _build_head(pen, R, 'girl')
            _head_paint(pen, ink, R, hd, 'girl', 'full')
            info['eye'] = tuple(None if e_ is None else e_['c'] for e_ in R.eyes)
        if 'arm' in parts:
            for nm in ('far', 'near'):
                if specs[nm].get('front', False):
                    a = arm_(nm)
                    if nm == 'near':
                        info.update(a)
    info['chin'] = R.proj(_surf(GIRL_FACE, GIRL_FACE[0][-1], 0.0)[None])[0]
    info['head_c'] = R.proj(np.float32([[0, 0, 0]]))[0]
    return info


# --------------------------------------------------------------------------- 他 · 动作
def _boy_group(pen, pose, sketch):
    if sketch:
        return pen.group(pose.get('name', 'boy'), boil=float(pose.get('boil', 2.1)), knock=False,
                         opacity=float(pose.get('opacity', 0.6)), bleed=0.7)
    return pen.group(pose.get('name', 'boy'), boil=float(pose.get('boil', 1.0)), bleed=1.0)


def _boy_construct(pen, ink, R, brk):
    """草稿的起形辅助线（同 boy()）：头部椭圆 + 十字中线、脊柱动势线、肩线。"""
    S, seed = R.S, R.seed
    hy, hw, hf, hb = _resample(_BY, [_BW, _BF, _BB], 16)
    G, ph = _rings(hy, hw * 1.03, hf + 0.01, hb - 0.01, 36)
    Pg = R.proj(G)
    hull = cv2.convexHull(np.round(Pg.reshape(-1, 2) * 4).astype(np.int32)).reshape(-1, 2).astype(np.float32) / 4
    hull = hull[::max(1, len(hull) // 16)]
    pen.line(hull, 0.013 * S, tone=0.36, role='construct', color='graphite', seed=seed + 1, closed=True, reps=2,
             spread=2.8, breaks=brk * 0.7)
    if R.back:
        return
    mer = R.proj(np.float32([[0.0, y, np.interp(y, _BY, _BF) + 0.012] for y in np.linspace(-0.47, 0.5, 9)]))
    pen.line(mer, 0.012 * S, tone=0.34, role='construct', color='graphite', seed=seed + 2, breaks=brk * 0.7)
    hwv, fr, bk = (np.interp(0.03, _BY, c) for c in (_BW, _BF, _BB))
    zc, hd_ = (fr + bk) / 2, (fr - bk) / 2
    eyl = [[hwv * math.cos(a) * 1.02, 0.03, zc + hd_ * math.sin(a)] for a in np.linspace(0.1, 0.95, 9) * math.pi]
    pen.line(R.proj(np.float32(eyl)), 0.012 * S, tone=0.34, role='construct', color='graphite', seed=seed + 3,
             breaks=brk * 0.7)
    spine = np.vstack([R.proj(np.float32([[0.0, -0.52, -0.08], [-0.05, 0.1, -0.42]])),
                       R.TB([(-0.22, 0.1), (-0.40, 0.6), (-0.46, 1.2), (-0.36, 1.8)])])
    ink.line(spine, 0.014 * S, tone=0.36, role='construct', color='graphite', seed=seed + 4, breaks=brk * 0.6)
    ink.line(R.TB([(0.62, 0.14), (0.0, 0.10), (-0.78, 0.24)]), 0.013 * S, tone=0.30, role='construct',
             color='graphite', seed=seed + 5, breaks=brk * 0.6)


def _boy_erase_marks(pen, R, er):
    """橡皮擦痕（同 boy()）。"""
    S, seed = R.S, R.seed
    hc = R.proj(np.float32([[0.0, -0.05, 0.0]]))[0]
    r = rng(seed, 990)
    for k in range(4):
        c0 = hc + np.float32([r.uniform(-0.5, 0.5) * S, (k * 0.55 - 0.2) * S])
        ang = math.radians(r.uniform(-35, -15))
        v = np.float32([math.cos(ang), math.sin(ang)])
        L = (0.6 + 0.9 * er) * S * min(1.0, er * 2.2 - k * 0.25)
        if L <= 4:
            continue
        poly, _, _ = tube([c0 - v * L / 2, c0 + v * L / 2 + np.float32([0, 0.04 * S])], [0.12 * S, 0.20 * S, 0.16 * S])
        pen.lift([poly], amt=0.85 * min(1.0, er * 1.6), seed=seed + 991 + k, soft=3.0, dry=0.6)
        pen.shade([poly], amount=0.05 * er, color='graphite', seed=seed + 995 + k, soft=6.0)


def _ik_low(shp, wr_t, l1, l2, pref=(0.0, 1.0)):
    """两种弯法里肘更靠 pref 方向（默认：更低）的那一种 → bend 符号。"""
    e1, _ = ik2(shp, wr_t, l1, l2, bend=1.0)
    e2, _ = ik2(shp, wr_t, l1, l2, bend=-1.0)
    pv = np.float32(pref)
    return 1.0 if float(np.dot(e1 - np.float32(shp), pv)) >= float(np.dot(e2 - np.float32(shp), pv)) else -1.0


def _boy_arm_x(pen, ink, R, shp, spec, sketch, seed, l1=1.15, l2=1.0):
    """他的一只手臂（肩在 shp）：spec 同她的（hand, shape, thumb, bend, elbow, hang, fwd, tool）。"""
    S, f = R.S, R.f
    shp = np.float32(shp)
    if spec.get('hang'):
        d = _unit(np.float32([float(spec.get('fwd', 0.06)) * f, 1.0]))
        hand = shp + d * (0.975 * (l1 + l2) * S + 0.10 * S)
    else:
        hand = np.float32(spec['hand'])
    if spec.get('elbow') is not None:
        elb = np.float32(spec['elbow'])
        wr = hand - _unit(hand - elb) * 0.12 * S
    else:
        dv = hand - shp
        wr_t = hand - _unit(dv) * 0.10 * S
        bd = spec.get('bend', 1.0 if f > 0 else -1.0)
        if bd == 'low':
            bd = _ik_low(shp, wr_t, l1 * S, l2 * S)
        elb, wr = ik2(shp, wr_t, l1 * S, l2 * S, bend=float(bd))
    _xtool_pre(pen, ink, R, spec, hand, seed)
    _sleeve_boy(ink, R, shp, elb, wr, seed, sketch)
    shape = spec.get('shape', 'flat')
    thumb = float(spec.get('thumb', -1)) * f
    _hand(ink, R, wr, hand, shape, thumb=thumb, seed=seed + 50, color='skin', role='sketch' if sketch else 'contour',
          fill=not sketch, size=1.05)
    out = dict(hand=hand, wrist=wr, elbow=elb, shoulder=shp)
    tool = spec.get('tool')
    if tool and tool[0] in ('spoon', 'soupspoon', 'ladle'):
        out['tool_tip'] = np.float32(tool[1])
    tipd = _unit(hand - wr)
    out['fingertip'] = wr + tipd * (0.27 if shape == 'open' else 0.20) * 1.05 * S
    return out


def _gait_leg(ph, step):
    """侧面走路的一条腿（相位 ph：0 脚跟着地、0–0.55 支撑往后、0.55–1 抬腿往前摆）。
    → (大腿角, 小腿角, 脚背角)，弧度，从竖直往前为正；脚背角 >0 = 脚尖朝下。"""
    ph = ph % 1.0
    A = 0.38 * step
    if ph < 0.55:
        a = A * (1.0 - 2.0 * ph / 0.55)
    else:
        x = (ph - 0.55) / 0.45
        a = -A + 2.0 * A * math.sin(0.5 * math.pi * x)
    # 膝：支撑期微屈；摆动期在 0.63 达到最大（约 50 度），0.95 前伸直
    if ph < 0.45:
        k = 0.06 * step
    elif ph < 0.63:
        k = step * (0.06 + 0.82 * float(smooth01((ph - 0.45) / 0.18)))
    elif ph < 0.95:
        k = step * (0.88 - 0.84 * float(smooth01((ph - 0.63) / 0.32)))
    else:
        k = 0.04 * step
    if ph < 0.06:
        fa = -0.18 * step * (1 - ph / 0.06)
    elif ph < 0.42:
        fa = 0.0
    elif ph < 0.58:
        fa = 0.70 * step * (ph - 0.42) / 0.16
    elif ph < 0.90:
        fa = step * (0.70 - 0.62 * (ph - 0.58) / 0.32)
    else:
        fa = step * (0.08 - 0.26 * (ph - 0.90) / 0.10)
    return a, a - k, fa


_BOY_SHOE = [(-0.12, -0.06), (0.08, -0.07), (0.34, 0.06), (0.36, 0.18), (-0.12, 0.19)]


def _side_leg_pts(hip, a, b, fa, kf=1.0):
    """侧面腿的关键点（局部 u 前 / v 下，单位 S）：髋 → 膝 → 踝 + 鞋（绕踝转 fa）。kf：前后方向的透视缩短。"""
    L1, L2 = 1.5, 1.52
    hip = np.float32(hip)
    knee = hip + np.float32([L1 * math.sin(a) * kf, L1 * math.cos(a)])
    ank = knee + np.float32([L2 * math.sin(b) * kf, L2 * math.cos(b)])
    c, s_ = math.cos(fa), math.sin(fa)
    shoe = np.float32([[ank[0] + (u * c - v * s_) * kf, ank[1] + (u * s_ + v * c)] for u, v in _BOY_SHOE])
    return hip, knee, ank, shoe


def _boy_leg_draw(pen, ink, R, P3, shoe, sketch, seed, shade=False):
    """一条腿（局部坐标的 髋/膝/踝 三点 + 鞋多边形）→ 裤管 + 鞋。"""
    S = R.S
    lc = 'graphite' if sketch else None
    P = R.T(np.float32(P3))
    poly, Ls_, Rs_ = tube(P, [0.34 * S, 0.25 * S, 0.19 * S])
    sp = spline(R.T(shoe), 1.5, closed=True)
    if not sketch:
        ink.cover([poly], seed=seed, feather=0.8)
        ink.fill([poly], 'boy_pants', seed=seed + 2)
        if shade:
            ink.shade([poly], amount=0.25, seed=seed + 4)
        ink.cover([sp], seed=seed + 10, feather=0.7)
        ink.fill([sp], BOY_SHOE, seed=seed + 12)
    ink.line(Ls_[::8], 0.026 * S, tone=0.75, seed=seed + 6, color=lc)
    ink.line(Rs_[::8], 0.022 * S, tone=0.65, seed=seed + 8, color=lc)
    ink.line(sp[::4], 0.024 * S, tone=0.85, seed=seed + 14, closed=True, color=lc, taper=(0.0, 0.0))
    # 膝盖的一道褶
    kv = _unit(P[2] - P[1])
    kn = _perp(kv)
    ink.line([P[1] - kn * 0.08 * S, P[1] + kv * 0.05 * S, P[1] + kn * 0.06 * S], 0.016 * S, tone=0.35,
             seed=seed + 16, color=lc, role='detail', taper=(0.3, 0.5))
    return poly


def _boy_back_walk(pen, ink, R, sketch, ph, step, arm_specs):
    """他的背影：走路（ph 相位、step 步幅），手臂可覆盖（arm_specs = dict(near=…, far=…)，同 _back_arm 的 spec）。"""
    S = R.S
    seed = R.seed + 500
    lc = 'graphite' if sketch else None
    out = {}
    for k, (u0, sg) in enumerate(((-0.22, -1), (0.22, 1))):
        p = (ph + (0.0 if sg > 0 else 0.5)) % 1.0
        lift = 0.20 * step * math.sin(math.pi * (p - 0.5) / 0.5) if p >= 0.5 else 0.0
        away = 0.06 * step * math.cos(2 * math.pi * p)          # 往前迈的那只脚更远（画面上更高一点）
        knee = (u0 * 0.98, 3.1 - 0.35 * lift - 0.3 * away)
        ank = (u0 * 1.0, 4.60 - lift - away)
        P = R.T([(u0 * 0.8, 1.6), knee, ank])
        poly, Ls_, Rs_ = tube(P, [0.34 * S, 0.24 * S, 0.19 * S])
        hh = 0.16 + 0.10 * lift / max(0.2 * step, 1e-3) if lift > 0 else 0.16
        heel = spline(R.T([(u0 - 0.11, ank[1] - 0.04), (u0 + 0.11, ank[1] - 0.04), (u0 + 0.12, ank[1] + hh),
                           (u0 - 0.12, ank[1] + hh)]), 1.5, closed=True)
        if not sketch:
            ink.cover([poly], seed=seed + k, feather=0.8)
            ink.fill([poly], 'boy_pants', seed=seed + 2 + k)
            ink.cover([heel], seed=seed + 8 + k, feather=0.7)
            ink.fill([heel], BOY_SHOE, seed=seed + 10 + k)
            if lift > 0.02:
                sole = spline(R.T([(u0 - 0.10, ank[1] + hh * 0.45), (u0 + 0.10, ank[1] + hh * 0.45),
                                   (u0 + 0.11, ank[1] + hh), (u0 - 0.11, ank[1] + hh)]), 1.5, closed=True)
                ink.shade([sole], amount=0.5, seed=seed + 20 + k)
        ink.line(Ls_[::8], 0.026 * S, tone=0.75, seed=seed + 4 + k, color=lc)
        ink.line(Rs_[::8], 0.022 * S, tone=0.65, seed=seed + 6 + k, color=lc)
        ink.line(heel[::4], 0.022 * S, tone=0.85, seed=seed + 12 + k, color=lc, closed=True, taper=(0.0, 0.0))
    specs = {}
    for nm, sg in (('near', 1), ('far', -1)):
        sp = arm_specs.get(nm)
        if sp is None:
            p = (ph + (0.5 if sg > 0 else 0.0)) % 1.0            # 手臂和同侧腿反向摆
            sw = math.cos(2 * math.pi * p) * step
            su = _BOY_BACK_SIDE[3][0] - 0.07
            shp = R.TB([(su * sg, 0.22)])[0]
            d = _unit(R.TB([((su + 0.12) * sg, 1.0)])[0] - R.TB([(su * sg, 0.0)])[0])
            hand = shp + d * (0.975 * 2.04 * S + 0.10 * S) + np.float32([-sg * 0.06 * S * max(sw, 0),
                                                                            -0.10 * S * abs(sw)])
            sp = dict(hand=hand, shape='flat', thumb=1)
        specs[nm] = dict(sp, _sketch=sketch, l1=sp.get('l1', 1.06), l2=sp.get('l2', 0.98))

    def slv(nm):
        sd_ = seed + (40 if nm == 'near' else 140)
        return lambda shp, elb, wr, hand, us: _sleeve_boy(ink, R, shp, elb, wr, sd_, sketch)
    for nm in ('far', 'near'):
        out[nm] = _back_arm(pen, ink, R, nm, specs[nm], ('boy_sweater', 'skin'), slv(nm),
                            seed + (40 if nm == 'near' else 140))
    if sketch:
        ink.hatch([spline(R.TB(_back_outline(_BOY_BACK_SIDE, 1.62)), 4.0, closed=True)], 70, 7, seed=seed + 39,
                  tone=0.30 * (1 - 0.6 * R.erase), color='graphite')
    sil = _back_torso(pen, ink, R, _BOY_BACK_SIDE, 1.62, 'boy_sweater', seed, sketch=sketch, lc=lc)
    out['sil'] = [sil]
    if sketch:
        ink.line(R.TB([(0.0, -0.05), (0.03, 0.6), (0.0, 1.2), (-0.02, 1.62)]), 0.014 * S, tone=0.34,
                 role='construct', color='graphite', seed=seed + 60)
        ink.line(R.TB([(-0.80, 0.16), (0.0, 0.10), (0.80, 0.17)]), 0.013 * S, tone=0.30, role='construct',
                 color='graphite', seed=seed + 61)
    return out


def _dust(pen, R, trace, origin, amt, wind, seed, color='graphite', density=1.0):
    """草稿化成灰：以 origin 为中心、半径随 amt 长大的一圈参差边界里的线被擦掉（lift），
    边界附近的线条碎成一粒粒灰，顺着 wind 飘走、变淡。trace = 人物轮廓上的点（场景坐标）。"""
    if amt <= 0.001 or trace is None or len(trace) == 0:
        return
    S = R.S
    T_ = np.asarray(trace, np.float32)
    o = np.float32(origin)
    dist = np.hypot(*(T_ - o).T)
    maxd = float(dist.max()) + 1e-3
    rad = float(amt) * 1.12 * maxd
    band = 0.55 * S
    r = rng(seed, 77)
    if rad > 2:
        th = np.linspace(0, 2 * math.pi, 48, endpoint=False)
        nz = _noise1(th / (2 * math.pi), sd(seed, 78), freq=7, octaves=2)
        rr = rad * (1.0 + 0.10 * nz) - 0.25 * band
        if rr.max() > 1:
            poly = np.stack([o[0] + np.maximum(rr, 0) * np.cos(th), o[1] + np.maximum(rr, 0) * np.sin(th)], 1)
            pen.lift([poly.astype(np.float32)], amt=1.0, seed=seed + 1, soft=0.10 * S, dry=0.5)
    w = _unit(np.float32(wind)) if np.hypot(*wind) > 1e-6 else np.float32([0, -1])
    wl = float(np.hypot(*wind)) if np.hypot(*wind) > 1e-6 else 1.0
    n = 0
    order = r.permutation(len(T_))
    for i in order:
        q = (rad - dist[i]) / band
        if q < -0.15 or q > 1.0:
            continue
        q = clamp(q, 0.0, 1.0)
        for j in range(3 if density >= 1 else 1):
            jit = r.normal(0, 1, 2).astype(np.float32)
            pos = T_[i] + w * wl * (0.15 + q) * 0.9 * S * (0.6 + 0.8 * r.random()) + \
                np.float32([0, -1]) * 0.25 * S * q + jit * 0.06 * S * (0.3 + q)
            sz = 0.022 * S * (1.0 - 0.55 * q) * (0.6 + 0.7 * r.random())
            pen.dot(pos[0], pos[1], sz, sz * (0.5 + 0.5 * r.random()), color, tone=0.85 * (1.0 - 0.75 * q),
                    seed=(seed, 3, int(i), j), rot=float(r.uniform(0, 180)))
            n += 1
        if n > 220 * density:
            break


def _densify_trace(polys, spacing):
    out = []
    for P in polys:
        P = np.asarray(P, np.float32).reshape(-1, 2)
        if len(P) >= 2:
            out.append(densify(P, spacing))
    return np.vstack(out) if out else np.zeros((0, 2), np.float32)


def _rise_geom(rise, f, kf=0.8):
    """从椅子上站起：rise 0..1 → (髋相对脚踝的局部坐标 u/v（单位 S，v 向下，脚底 v=0）, 前倾 lean)。"""
    r_ = float(clamp(rise))
    hs = (-1.28 * kf, -1.84)
    ht = (-0.04, -3.20)
    qx = float(smooth01(r_ / 0.55))
    qy = float(smooth01((r_ - 0.22) / 0.78))
    hip = (hs[0] + (ht[0] - hs[0]) * qx, hs[1] + (ht[1] - hs[1]) * qy)
    lean = 0.10 * (1 - r_) + 0.55 * math.sin(math.pi * clamp(r_ / 0.9)) ** 1.2
    return hip, lean


def boy_act(pen, pose, mode='sketch'):
    """他的动作（第 4/6/8 镜）。和 boy() 同一个人、同一套头/身体/袖子/手，只是姿态更多。pose 字典同 boy()
    （x, y, s, facing, yaw, pitch, roll, face, blink, breath, light, seed, boil, opacity, erase, clip_y/clip_poly），另外：
      act = 'reach'  坐在桌后，近侧手伸向桌上的东西：target 指尖要碰到的点；u 0..1 伸手进度；rest 手的起点（可省）；
                     远侧前臂平放在桌上（far_hand 可省）。info['fingertip'] 当前指尖位置。
            'feed'   坐在桌后，远侧手拿金属汤勺喂她：target = 她的嘴（girl_mouth_point）；u 0..1：0 勺子在自己嘴边
                     （配 face='blow' 吹凉）→ 1 送到她嘴边；bowl=(cx,cy) 他自己的碗（近侧手扶着；可省）；bowl_r。
                     够不着时自动前倾。info['tool_tip'] 勺头中心。
            'rise'   从椅子上站起（全身）：rise 0..1；x = 脚踝的 x，floor = 地面 y（鞋底）；table=(x,y) 起身时双手撑着的
                     桌沿点（可省；rise>0.45 后手离开桌面垂下）。kf 前后透视缩短（默认 0.8）。
            'walk'   走路（全身）：gait 相位（周期 1，一步半个周期）、step 步幅 0..1（默认 1）、back=True 背影
                     （走向画面里面）；floor 可省（不写 = 用 y 作颈根，身体随步子轻微起伏）。
            'door'   背对镜头开门：同 walk(back=True)，近侧手（画面右边那只）抬起抓门把手：handle=(x,y)，u 0..1 抬手；
                     door_side='right'|'left' 用哪只手。
            'stand'  站着（全身），手臂用 arm_near / arm_far 覆盖（dict(hand, shape, thumb, bend, front)，不写 = 垂下）。
      所有 act 都可用 arm_near / arm_far 覆盖手臂。
      dust 0..1：草稿化成灰散掉（只在 sketch 里有意义）——dust_from 起点（默认 reach 的指尖 / 头），wind 飘散方向
                 （场景坐标向量，默认往上偏后），dust_color（默认 'graphite'）。erase 同 boy()（断线 + 橡皮擦痕）。
    返回 info：hands {near, far}、hand（主要那只）、fingertip、tool_tip、head_c、chin、mouth、neck、sil、trace（轮廓点）。"""
    sketch = mode == 'sketch'
    act = pose.get('act', 'stand')
    p = dict(pose)
    back = bool(p.get('back', False))
    if act == 'door':
        back = True
        p['back'] = True
    f0 = 1 if (back or p.get('facing', -1) >= 0) else -1
    S0 = float(p.get('s', 126))
    gait = float(p.get('gait', 0.0))
    step = float(p.get('step', 1.0))
    legs_side = None
    if act in ('reach', 'feed', 'sit'):
        p['pose'] = 'sit_x'
    else:
        p['pose'] = 'stand'
    kf = float(p.get('kf', 0.8))
    if act == 'rise':
        hip, ln = _rise_geom(p.get('rise', 0.0), f0, kf)
        fl = float(p.get('floor', p['y'] + 4.81 * S0))
        ax = float(p['x'])
        p['x'] = ax + hip[0] * S0 * f0
        p['y'] = fl + hip[1] * S0 - 1.6 * S0
        p['lean'] = float(p.get('lean', 0.0)) + ln
        ank = (-hip[0], -0.19 - hip[1])            # 踝相对髋（局部，单位 S）
        legs_side = ('rise', ank)
    elif act in ('walk', 'door') and not back:
        legs = []
        lows = []
        for k, ph_ in enumerate((gait + 0.5, gait)):             # 远侧、近侧
            a, b, fa = _gait_leg(ph_, step)
            pts = _side_leg_pts((0.04 - 0.10 * k, 1.6), a, b, fa)
            legs.append((ph_, pts))
            lows.append(float(pts[3][:, 1].max()))
        bob = max(lows) - 4.81
        if p.get('floor') is not None:
            p['y'] = float(p['floor']) - (1.6 + (max(lows) - 1.6)) * S0
        else:
            p['y'] = float(p['y']) - bob * S0
        p['lean'] = float(p.get('lean', 0.06))
        legs_side = ('walk', legs)
    elif back and act in ('walk', 'door'):
        bob = 0.035 * step * math.cos(4 * math.pi * gait)
        if p.get('floor') is not None:
            p['y'] = float(p['floor']) - 4.79 * S0
        p['y'] = float(p['y']) - bob * S0
    R = _BoyRig(p)
    S, f = R.S, R.f
    er = R.erase
    brk = 0.62 * er if sketch else 0.0
    ink = _Ink(pen, S, clip=R.clip, breaks=brk, sketch=sketch,
               role_map={'contour': 'sketch', 'detail': 'sketch', 'feature': 'sketch'} if sketch else None)
    ink_a = _Ink(pen, S, clip=None, breaks=brk, sketch=sketch,
                 role_map={'contour': 'sketch', 'detail': 'sketch', 'feature': 'sketch'} if sketch else None)
    seed = R.seed
    info = dict(hands={})
    trace = []
    near_sh = R.TB([(-0.62, 0.28)])[0]
    far_sh = R.TB([(0.44, 0.20)])[0]
    an, af = p.get('arm_near'), p.get('arm_far')
    front_far = False
    # ---------------- 手臂姿态
    if act == 'reach':
        tgt = np.float32(p['target'])
        u = float(smooth01(p.get('u', 1.0)))
        rest = np.float32(p.get('rest', R.TB([(0.30, 1.16)])[0]))
        tip = lerp(rest + np.float32([0.10 * S * f, 0.0]), tgt, u)
        d = _unit(tip - near_sh)
        hand = tip - d * 0.17 * 1.05 * S
        an = an or dict(hand=hand, shape='open' if u > 0.15 else 'flat', thumb=-1)
        af = af or dict(hand=np.float32(p.get('far_hand', R.TB([(0.05, 1.12)])[0])),
                        elbow=np.float32(p.get('far_elbow', R.TB([(0.62, 1.04)])[0])), shape='fist', thumb=-1)
        front_far = True
    elif act == 'feed':
        mt = np.float32(p['target'])
        u = float(smooth01(p.get('u', 1.0)))
        dv1 = _unit(np.float32([-f * 0.93, 0.37]))
        c1 = mt + dv1 * 0.15 * S + np.float32([0, 0.045 * S])
        myq = R.proj(_surf(BOY_FACE, BOY_FEAT['mouth_y'], 0.0, dz=0.01)[None])[0]
        dv0 = _unit(np.float32([f * 0.42, 0.91]))
        c0 = myq + np.float32([f * 0.20 * S, 0.05 * S])
        c = lerp(c0, c1, u) + np.float32([0, -0.10 * S * math.sin(math.pi * u)])
        dv = _unit(lerp(dv0, dv1, u))
        hand = c + dv * 0.62 * S
        # 够不着就往前倾（以臀为轴）
        reach = (1.15 + 1.0) * S * 0.97
        for _ in range(6):
            fs = R.TB([(0.44, 0.20)])[0]
            if float(np.hypot(*(hand - fs))) <= reach or R.lean > 0.9:
                break
            R.lean += 0.08
            R.proj = HeadProj(R.TB([(0.10, -0.40)])[0], S, p.get('yaw', 36), p.get('pitch', -6), p.get('roll', 7),
                              flip=f)
            hu_ = R.proj(np.float32([[0, -0.2, 0.3]]))[0] - R.proj(np.float32([[0, 0.2, 0.3]]))[0]
            R.head_up = _unit(hu_)
        near_sh = R.TB([(-0.62, 0.28)])[0]
        far_sh = R.TB([(0.44, 0.20)])[0]
        af = af or dict(hand=hand, shape='fist', thumb=1, tool=('soupspoon', c, float(p.get('soup', 1.0))),
                        bend='low')
        bw = p.get('bowl')
        if bw is not None:
            bw = np.float32(bw)
            br_ = float(p.get('bowl_r', 0.24 * S))
            an = an or dict(hand=bw + np.float32([0.62 * br_ * -f, 0.25 * br_]), shape='cup', thumb=1,
                            tool=('bowl', bw, br_))
        else:
            an = an or dict(hand=R.TB([(0.25, 1.14)])[0], shape='flat', thumb=-1)
        front_far = True
        info['tool_tip'] = c
    elif act == 'rise':
        tb = p.get('table')
        k_ = float(smooth01((float(p.get('rise', 0.0)) - 0.45) / 0.40))
        hn = dict(hang=True, fwd=0.20, shape='flat', thumb=-1)
        if tb is not None and k_ < 1.0:
            tb = np.float32(tb)
            hg = near_sh + _unit(np.float32([0.2 * f, 1.0])) * (0.975 * 2.15 * S + 0.1 * S)
            an = an or dict(hand=lerp(tb, hg, k_), shape='flat', thumb=-1)
            hgf = far_sh + _unit(np.float32([0.2 * f, 1.0])) * (0.975 * 2.15 * S + 0.1 * S)
            af = af or dict(hand=lerp(tb + np.float32([0.25 * S * f, -0.02 * S]), hgf, k_), shape='flat', thumb=-1)
        an = an or hn
        af = af or dict(hang=True, fwd=0.16, shape='flat', thumb=1)
    elif act in ('walk', 'stand') and not back:
        sw = math.cos(2 * math.pi * gait) * step if act == 'walk' else 0.0

        def swing(shp, s_):
            ang = 0.38 * s_
            L = 0.975 * 2.15 * S + 0.10 * S
            d = np.float32([math.sin(ang) * f, math.cos(ang)])
            return dict(hand=shp + d * L * (1 - 0.06 * abs(s_)), shape='flat', thumb=-1, bend=-f)
        an = an or swing(near_sh, sw)
        af = af or swing(far_sh, -sw)
    elif back:
        if act == 'door':
            ds = p.get('door_side', 'right')
            h = np.float32(p['handle'])
            u = float(smooth01(p.get('u', 1.0)))
            su = _BOY_BACK_SIDE[3][0] - 0.07
            sg = 1 if ds == 'right' else -1
            shp = R.TB([(su * sg, 0.22)])[0]
            d = _unit(R.TB([((su + 0.12) * sg, 1.0)])[0] - R.TB([(su * sg, 0.0)])[0])
            hang = shp + d * (0.975 * 2.04 * S + 0.10 * S)
            spec = dict(hand=lerp(hang, h, u), shape='fist' if u > 0.6 else 'flat', thumb=1, bend=-sg)
            if sg > 0:
                an = an or spec
            else:
                af = af or spec
    # ---------------- 画
    with _boy_group(pen, p, sketch):
        if sketch:
            _boy_construct(pen, ink, R, brk)
        if back:
            ob = _boy_back_walk(pen, ink, R, sketch, gait if act in ('walk', 'door') else 0.0,
                                step if act in ('walk', 'door') else 0.0,
                                dict(near=an, far=af))
            info['hands'] = {nm: ob[nm]['hand'] for nm in ('near', 'far')}
            info['shoulders'] = {nm: ob[nm]['shoulder'] for nm in ('near', 'far')}
            info['sil'] = ob['sil']
            info['hand'] = ob['near']['hand'] if (act != 'door' or p.get('door_side', 'right') == 'right') \
                else ob['far']['hand']
            for nm in ('near', 'far'):
                trace += [np.float32([ob[nm]['shoulder'], ob[nm]['elbow'], ob[nm]['wrist'], ob[nm]['hand']])]
            trace.append(R.T([(-0.22, 1.6), (-0.22, 3.1), (-0.22, 4.6)]))
            trace.append(R.T([(0.22, 1.6), (0.22, 3.1), (0.22, 4.6)]))
        else:
            # 远侧手臂在身后（垂着 / 摆在身后）
            if af is not None and not front_far:
                a = _boy_arm_x(pen, ink_a, R, far_sh, af, sketch, seed + 140)
                info['hands']['far'] = a['hand']
                trace.append(np.float32([a['shoulder'], a['elbow'], a['wrist'], a['hand']]))
            # 腿
            if legs_side is not None and legs_side[0] == 'walk':
                for k, (ph_, (hp, kn, ak, shoe)) in enumerate(legs_side[1]):
                    _boy_leg_draw(pen, ink, R, [hp, kn, ak], shoe, sketch, seed + 300 + 20 * k, shade=(k == 0))
                    trace.append(R.T(np.float32([hp, kn, ak])))
            elif legs_side is not None and legs_side[0] == 'rise':
                ank = legs_side[1]
                for k, du in enumerate((0.07, -0.09)):
                    hp = np.float32([du * 0.6, 1.6])
                    ak = np.float32([ank[0] + du, 1.6 + ank[1]])
                    e, w_ = ik2(hp * np.float32([1, 1]), ak, 1.5, 1.52, bend=-1.0)
                    knee = np.float32(e)
                    shoe = np.float32([[ak[0] + u_ * kf, ak[1] + v_] for u_, v_ in _BOY_SHOE])
                    _boy_leg_draw(pen, ink, R, [hp, knee, ak], shoe, sketch, seed + 300 + 20 * k, shade=(k == 0))
                    trace.append(R.T(np.float32([hp, knee, ak])))
            elif R.body == 'stand':
                _boy_legs(pen, ink, R, sketch)
                trace.append(R.T([(0.0, 1.6), (0.0, 3.1), (0.0, 4.6)]))
            _boy_torso(pen, ink, R, sketch)
            front, bk, hem = R.torso()
            trace.append(R.TB(front))
            trace.append(R.TB(bk))
            if act == 'feed':
                hd = _build_head(pen, R, 'boy')
                _head_paint(pen, ink, R, hd, 'boy', 'sketch' if sketch else 'full')
                if an is not None:
                    a = _boy_arm_x(pen, ink_a, R, near_sh, an, sketch, seed + 40)
                    info['hands']['near'] = a['hand']
                    trace.append(np.float32([a['shoulder'], a['elbow'], a['wrist'], a['hand']]))
                a = _boy_arm_x(pen, ink_a, R, far_sh, af, sketch, seed + 140)
                info['hands']['far'] = a['hand']
                info['hand'] = a['hand']
                trace.append(np.float32([a['shoulder'], a['elbow'], a['wrist'], a['hand']]))
            else:
                if af is not None and front_far:
                    a = _boy_arm_x(pen, ink_a, R, far_sh, af, sketch, seed + 140)
                    info['hands']['far'] = a['hand']
                    trace.append(np.float32([a['shoulder'], a['elbow'], a['wrist'], a['hand']]))
                hd = _build_head(pen, R, 'boy')
                _head_paint(pen, ink, R, hd, 'boy', 'sketch' if sketch else 'full')
                if an is not None:
                    a = _boy_arm_x(pen, ink_a, R, near_sh, an, sketch, seed + 40)
                    info['hands']['near'] = a['hand']
                    info['hand'] = a['hand']
                    info['fingertip'] = a['fingertip']
                    trace.append(np.float32([a['shoulder'], a['elbow'], a['wrist'], a['hand'], a['fingertip']]))
        if back:
            hd = _build_head(pen, R, 'boy')
            _head_paint(pen, ink, R, hd, 'boy', 'sketch' if sketch else 'full')
        # 头的轮廓点
        hy, hw, hf, hb = _resample(_BY, [_BW, _BF, _BB], 10)
        G, _ = _rings(hy, hw * 1.05, hf + 0.03, hb - 0.03, 16)
        Pg = R.proj(G).reshape(-1, 2)
        trace.append(cv2.convexHull(Pg.astype(np.float32)).reshape(-1, 2))
        if sketch and er > 0.001:
            _boy_erase_marks(pen, R, er)
        tr = _densify_trace(trace, max(4.0, 0.07 * S))
        dust = float(p.get('dust', 0.0))
        if dust > 0.001:
            org = p.get('dust_from')
            if org is None:
                org = info.get('fingertip', R.proj(np.float32([[0, 0, 0]]))[0])
            wind = p.get('wind', (0.35 * -f, -1.0))
            _dust(pen, R, tr, org, dust, wind, seed + 1700, color=p.get('dust_color', 'graphite'))
    info['trace'] = tr
    info['head_c'] = R.proj(np.float32([[0, 0, 0]]))[0]
    info['chin'] = R.proj(np.float32([[0.0, 0.48, 0.24]]))[0]
    info['mouth'] = R.proj(_surf(BOY_FACE, BOY_FEAT['mouth_y'], 0.0, dz=0.01)[None])[0]
    info['neck'] = R.TB([(0.0, 0.0)])[0]
    return info


# --------------------------------------------------------------------------- 两人 · 窗边（第 7 镜 + T2）
def _couple_kiss_solve(bp, target, lean0=0.12, pitch0=22.0):
    """调他的 lean、pitch，让他的嘴落到 target（她的额头）上。→ (lean, pitch)。"""
    x = np.float64([lean0, pitch0])

    def F(v):
        q = dict(bp, lean=float(v[0]), pitch=float(v[1]))
        return np.float64(boy_mouth_point(q)) - np.float64(target)
    for _ in range(8):
        r0 = F(x)
        if float(np.hypot(*r0)) < 0.3:
            break
        J = np.zeros((2, 2))
        for j, h in enumerate((0.01, 0.5)):
            dx = np.zeros(2)
            dx[j] = h
            J[:, j] = (F(x + dx) - r0) / h
        try:
            st = np.linalg.solve(J, -r0)
        except np.linalg.LinAlgError:
            break
        x = x + np.clip(st, [-0.25, -12.0], [0.25, 12.0])
        x[0] = float(np.clip(x[0], -0.2, 0.9))
        x[1] = float(np.clip(x[1], -10.0, 50.0))
    return float(x[0]), float(x[1])


def couple_poses(pose):
    """couple() 用到的两个人的 pose（girl/boy 的 pose 字典），不画。场景可以拿来算对位、剪影、光晕。
    → dict(girl=她的 pose, boy=他的 pose, kiss=接吻程度, hug, forehead=她额头点, mouth=他嘴的点, gap)。"""
    s = float(pose['s'])
    xg, yg = float(pose['x']), float(pose['y'])
    fg = 1 if pose.get('side', 1) >= 0 else -1
    k = float(clamp(pose.get('k', 0.0)))
    hug = float(smooth01(pose.get('hug', 0.0)))
    la = float(smooth01(pose.get('look_away', 0.0)))
    up = float(smooth01(pose.get('look_up', 0.0)))
    kiss = float(smooth01(k)) * (1.0 - hug) * (1.0 - 0.45 * up)
    Sb = 1.08 * s
    gap = float(pose.get('gap', 1.22 + (0.98 - 1.22) * hug))
    xb = xg + fg * gap * s
    yb = yg - float(pose.get('dh', 0.50)) * s
    br = float(pose.get('breath', 0.0))
    body = pose.get('body', 'stand')
    # 她：亲额头时微微仰脸（look_up 时睁眼抬头看他）→ 靠在他胸口（低头、头往他那边歪、上身前倾）
    g = dict(x=xg, y=yg, s=s, facing=fg, body=body, seed=int(pose.get('seed', 1000)), boil=float(pose.get('boil', 1.0)),
             breath=br, light=float(pose.get('light', 1.0)), blink=float(pose.get('blink', 0.0)))
    g['yaw'] = 50.0 + 4.0 * kiss - 6.0 * up + (66.0 - 50.0) * hug
    g['pitch'] = -3.0 - 5.0 * kiss - 12.0 * up * (1 - hug) + 19.0 * hug
    g['roll'] = 3.0 * kiss + 12.0 * hug
    g['lean'] = 0.02 + 0.03 * kiss + 0.22 * hug
    face = pose.get('her_face')
    if face is None:
        face = mix_expr(mix_expr('gentle', 'peace', smooth01(k * 1.6)), 'peace', hug)
        if up > 0:
            look = dict(EXPR['gentle'], gx=0.55, gy=-0.45, open=0.70, wet=0.8, blush=0.8)
            face = mix_expr(face, look, up * (1 - hug))
    g['face'] = face
    for kk in ('clip_y', 'clip_poly'):
        if pose.get(kk) is not None:
            g[kk] = pose[kk]
    # 他
    b = dict(x=xb, y=yb, s=Sb, facing=-fg, pose='stand', seed=int(pose.get('boy_seed', 2000)),
             boil=float(pose.get('boy_boil', pose.get('boil', 1.0))), breath=br + 0.35,
             light=float(pose.get('boy_light', -float(pose.get('light', 1.0)))),
             blink=float(pose.get('boy_blink', 0.0)), erase=float(pose.get('boy_erase', 0.0)))
    b['yaw'] = 50.0 + 4.0 * hug
    b['pitch'] = -2.0 + 22.0 * hug
    b['roll'] = 6.0 * hug
    b['lean'] = 0.03 + 0.06 * hug
    for kk in ('clip_y', 'clip_poly'):
        if pose.get(kk) is not None:
            b[kk] = pose[kk]
    fh = girl_forehead_point(g)
    if kiss > 0.001:
        lk, pk = _couple_kiss_solve(dict(b, yaw=b['yaw'] + 4.0, roll=b['roll'] + 4.0), fh)
        b['lean'] = b['lean'] + (lk - b['lean']) * kiss
        b['pitch'] = b['pitch'] + (pk - b['pitch']) * kiss
        b['yaw'] = b['yaw'] + 4.0 * kiss
        b['roll'] = b['roll'] + 4.0 * kiss
    # 他转头望向窗外（默认转向背对她的那一侧）
    if la > 0:
        b['yaw'] = b['yaw'] + (float(pose.get('away_yaw', -28.0)) - b['yaw']) * la
        b['pitch'] = b['pitch'] + (float(pose.get('away_pitch', -6.0)) - b['pitch']) * la
        b['roll'] = b['roll'] * (1 - la)
    bf = pose.get('his_face')
    if bf is None:
        bf = mix_expr('gentle', 'kiss_close', smooth01((kiss - 0.55) / 0.40))
        if up > 0:
            bf = mix_expr(bf, dict(EXPR['gentle'], gx=0.3, gy=0.75, open=0.55), up * (1 - hug))
        bf = mix_expr(bf, 'gentle', hug)
        if la > 0:
            bf = mix_expr(bf, dict(EXPR['distant'], gx=0.55), la)
    b['face'] = bf
    mo = boy_mouth_point(b)
    return dict(girl=g, boy=b, kiss=kiss, hug=hug, forehead=fh, mouth=mo, gap=gap)


def couple(pen, pose):
    """第 7 镜 + T2 · 窗边两人相对（中近景，腰部以上；身体照样画全身，画框以外的自然裁掉）。
    她在左边朝右（side=1，默认；side=-1 左右对调），他在右边朝左，比她高半个头，同一个地面。pose:
      x, y        她的颈根（场景坐标）    s  她的头高（他 = 1.08 s）    gap 两人颈根间距（单位 s；默认随 hug 从 1.22 → 0.98）
      dh          他的颈根比她高多少（单位 s，默认 0.5 = 同一地面）
      k           0..1 他低头靠近、嘴唇贴到她额头（k=1 时正好贴上，自动对位：girl_forehead_point ↔ boy_mouth_point）
      look_up     0..1 亲完以后她睁眼、抬头看他（温柔）
      hug         0..1 从“亲额头”过渡到“她把脸靠在他胸口”：她低头、头往他那边歪、上身前倾；他双臂环到她背后
                  （hug 会自动把 k 的姿态收掉）
      look_away   0..1 他（抱着她）把头转向画面另一侧的窗外；away_yaw（默认 -28 度）、away_pitch（默认 -6）
      loosen      0..1 他的手臂慢慢松开、垂到身侧
      her_face / his_face  覆盖表情（默认：她 gentle → peace（闭眼）→ look_up 时睁眼看他；他 gentle → kiss_close →
                  抱着时 gentle → look_away 时 distant）
      blink / boy_blink、breath、light（她的受光侧，他自动取反，boy_light 覆盖）、seed / boy_seed、boil / boy_boil
      boy_mode    'full'（默认；T2 的 C 一侧也是上色的他）/'sketch'（boy_opacity）
      body        'stand'（默认）/'upper'；clip_y/clip_poly 两人都裁（窗台、前景）
    画的顺序（从后往前）：他远侧的手（绕到她背后，只在她背后露出一点）→ 他的身体 → 她的身体 → 她远侧的手（他胸前）
    → 她的头 → 她近侧的手 → 他近侧的手臂（环过她的背）→ 他的头（亲额头时嘴唇压在她刘海上）。
    返回 info：girl / boy（两人的 pose）、forehead、mouth、boy_head_c、girl_head_c、hands（四只手的位置）、kiss。"""
    cp = couple_poses(pose)
    g, b = cp['girl'], cp['boy']
    hug = cp['hug']
    lo = float(smooth01(pose.get('loosen', 0.0)))
    sketch = pose.get('boy_mode', 'full') == 'sketch'
    Rg = _GirlRig(g)
    Rb = _BoyRig(b)
    s, Sb = Rg.S, Rb.S
    inkg = _Ink(pen, s, clip=Rg.clip)
    rm = {'contour': 'sketch', 'detail': 'sketch', 'feature': 'sketch'} if sketch else None
    inkb = _Ink(pen, Sb, clip=Rb.clip, sketch=sketch, role_map=rm)
    inkb_a = _Ink(pen, Sb, clip=None, sketch=sketch, role_map=rm)
    # ---- 手的目标点
    TBg, TBb = Rg.TB, Rb.TB
    b_near_sh = TBb([(-0.40, 0.27)])[0] + np.float32([0, 0.5 * Rb.br])
    b_far_sh = TBb([(0.38, 0.20)])[0] + np.float32([0, 0.5 * Rb.br])
    L1b, L2b = 1.15 * Sb, 1.0 * Sb

    def hang_b(shp, fwd):
        return shp + _unit(np.float32([fwd * Rb.f, 1.0])) * (0.975 * (L1b + L2b) + 0.10 * Sb)
    hn = lerp(TBg([(-0.05, 1.22)])[0], TBg([(-0.30, 0.60)])[0], hug)
    hf = lerp(TBg([(0.05, 1.30)])[0], TBg([(-0.22, 0.86)])[0], hug)
    hn = lerp(hn, hang_b(b_near_sh, 0.10), lo)
    hf = lerp(hf, hang_b(b_far_sh, 0.06), lo)
    g_near_sh = TBg([(-0.36, 0.22)])[0] + np.float32([0, 0.5 * Rg.br])
    g_far_sh = TBg([(0.28, 0.18)])[0] + np.float32([0, 0.5 * Rg.br])
    # 亲额头：两手轻轻搭在他胸前；靠在他胸口：两手蜷在两人之间（攥着他胸前的毛衣，肘垂下）
    g_near = lerp(TBb([(0.50, 0.86)])[0], g_near_sh + np.float32([0.86 * s * Rg.f, 0.36 * s]), hug)
    g_far = lerp(TBb([(0.46, 0.58)])[0], g_far_sh + np.float32([0.30 * s * Rg.f, 0.06 * s]), hug)

    def bend_for(shp, hand, l1, l2, S_, back_f):
        wr_t = hand - _unit(hand - shp) * 0.10 * S_
        return _ik_low(shp, wr_t, l1, l2, pref=(-0.6 * back_f, 0.8))
    shp_g = 'fist' if hug > 0.5 else 'flat'
    spec_gn = dict(hand=g_near, shape=shp_g, thumb=-1, bend=bend_for(g_near_sh, g_near, 1.10 * s, 0.96 * s, s, Rg.f))
    spec_gf = dict(hand=g_far, shape='flat', thumb=-1, bend=bend_for(g_far_sh, g_far, 1.10 * s, 0.96 * s, s, Rg.f))
    spec_bn = dict(hand=hn, shape='flat', thumb=1, bend=bend_for(b_near_sh, hn, L1b, L2b, Sb, 0.0))
    spec_bf = dict(hand=hf, shape='flat', thumb=1, bend=bend_for(b_far_sh, hf, L1b, L2b, Sb, 0.0))
    info = dict(girl=g, boy=b, forehead=cp['forehead'], mouth=cp['mouth'], kiss=cp['kiss'], hands={})
    if sketch:
        def bctx(nm):
            return pen.group(nm, boil=float(pose.get('boy_boil', 2.1)), knock=False,
                             opacity=float(pose.get('boy_opacity', 0.6)), bleed=0.7)
    else:
        def bctx(nm):
            return pen.group(nm, boil=float(b.get('boil', 1.0)), bleed=1.0)
    # 1–2. 他：远侧手臂（绕到她背后）+ 身体
    with bctx('boy'):
        a = _boy_arm_x(pen, inkb_a, Rb, b_far_sh, spec_bf, sketch, Rb.seed + 140)
        info['hands']['boy_far'] = a['hand']
        if pose.get('body', 'stand') == 'stand':
            _boy_legs(pen, inkb, Rb, sketch)
        _boy_torso(pen, inkb, Rb, sketch)
    # 3–7. 她
    with pen.group('girl', boil=float(g.get('boil', 1.0)), bleed=1.1):
        _girl_body(pen, inkg, Rg)
        a = _girl_arm_at(pen, inkg, Rg, g_far_sh, spec_gf, Rg.seed + 140)
        info['hands']['girl_far'] = a['hand']
        hd = _build_head(pen, Rg, 'girl')
        _head_paint(pen, inkg, Rg, hd, 'girl', 'full')
        a = _girl_arm_at(pen, inkg, Rg, g_near_sh, spec_gn, Rg.seed + 40)
        info['hands']['girl_near'] = a['hand']
    # 8–9. 他：近侧手臂 + 头
    with bctx('boy_front'):
        a = _boy_arm_x(pen, inkb_a, Rb, b_near_sh, spec_bn, sketch, Rb.seed + 40)
        info['hands']['boy_near'] = a['hand']
        hd = _build_head(pen, Rb, 'boy')
        _head_paint(pen, inkb, Rb, hd, 'boy', 'sketch' if sketch else 'full')
    info['boy_head_c'] = Rb.proj(np.float32([[0, 0, 0]]))[0]
    info['girl_head_c'] = Rg.proj(np.float32([[0, 0, 0]]))[0]
    return info
