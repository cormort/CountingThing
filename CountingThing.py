import streamlit as st
import random
import math

# --- 遊戲設定 (Configuration) ---

# 定義所有可用的Emoji主題 (已新增臉部表情)
EMOJI_THEMES = [
    { "name": "動物", "items": ['🐶', '🐱', '🐭', '🦊', '🐻', '🐼', '🐨', '🐯', '🐰', '🐷', '🐸', '🐵'] },
    { "name": "恐龍", "items": ['🦖', '🦕', '🐊', '🐉', '🐲', '🦎', '🐍', '🐢', '🦤', '🦚', '🦢', '🦜'] },
    { "name": "食物", "items": ['🍎', '🍌', '🍉', '🍇', '🍓', '🍒', '🍑', '🍍', '🥝', '🍔', '🍕', '🍩'] },
    { "name": "表情", "items": ['😄', '😠', '😢', '😂', '😮', '🤔', '😴', '😎', '😍', '😭', '😉', '😐'] },
]

# 定義每個區域的名稱和對應的Emoji索引
ZONE_DEFINITIONS = [
    { "name": '在長方形裡面', "type": 'rect-only', "emoji_idx": 0 },
    { "name": '在圓形裡面', "type": 'circle-only', "emoji_idx": 1 },
    { "name": '在三角形裡面', "type": 'tri-only', "emoji_idx": 2 },
    { "name": '在長方形和圓形裡面', "type": 'rect-circle', "emoji_idx": 3 },
    { "name": '在長方形和三角形裡面', "type": 'rect-tri', "emoji_idx": 4 },
    { "name": '在圓形和三角形裡面', "type": 'circle-tri', "emoji_idx": 5 },
    { "name": '在三個圖形裡面', "type": 'all-three', "emoji_idx": 6 },
    { "name": '在所有圖形外面', "type": 'outside', "emoji_idx": 7 },
    { "name": '在長方形邊上', "type": 'rect-border', "emoji_idx": 8 },
    { "name": '在圓形邊上', "type": 'circle-border', "emoji_idx": 9 },
    { "name": '在三角形邊上', "type": 'tri-border', "emoji_idx": 10 },
]

# --- 固定圖形尺寸與位置 (Geometric Definitions) ---
CANVAS_W, CANVAS_H = 900, 400
RECT = { "x": 50, "y": 120, "width": 400, "height": 220 }
CIRCLE = { "cx": 650, "cy": 230, "r": 120 }
TRI = { "v": [ {"x": 250, "y": 50}, {"x": 750, "y": 50}, {"x": 500, "y": 300} ] }
ITEM_SIZE = 40
MIN_DISTANCE_SQ = 45 * 45

# --- 幾何判斷輔助函式 (Geometric Helper Functions) ---

def is_inside_rect(p):
    return RECT['x'] <= p['x'] <= RECT['x'] + RECT['width'] and \
           RECT['y'] <= p['y'] <= RECT['y'] + RECT['height']

def is_inside_circle(p):
    return math.hypot(p['x'] - CIRCLE['cx'], p['y'] - CIRCLE['cy']) <= CIRCLE['r']

def is_inside_triangle(p):
    v = TRI['v']
    def sign(p1, p2, p3):
        return (p1['x'] - p3['x']) * (p2['y'] - p3['y']) - (p2['x'] - p3['x']) * (p1['y'] - p3['y'])
    d1 = sign(p, v[0], v[1])
    d2 = sign(p, v[1], v[2])
    d3 = sign(p, v[2], v[0])
    has_neg = (d1 < 0) or (d2 < 0) or (d3 < 0)
    has_pos = (d1 > 0) or (d2 > 0) or (d3 > 0)
    return not (has_neg and has_pos)

def dist_to_line_segment(p, v, w):
    l2 = (v['x'] - w['x'])**2 + (v['y'] - w['y'])**2
    if l2 == 0: return math.hypot(p['x'] - v['x'], p['y'] - v['y'])
    t = max(0, min(1, ((p['x'] - v['x']) * (w['x'] - v['x']) + (p['y'] - v['y']) * (w['y'] - v['y'])) / l2))
    projection = {'x': v['x'] + t * (w['x'] - v['x']), 'y': v['y'] + t * (w['y'] - v['y'])}
    return math.hypot(p['x'] - projection['x'], p['y'] - projection['y'])

def is_on_rect_border(p):
    on_horizontal = (abs(p['y'] - RECT['y']) < 2 or abs(p['y'] - (RECT['y'] + RECT['height'])) < 2) and RECT['x'] <= p['x'] <= RECT['x'] + RECT['width']
    on_vertical = (abs(p['x'] - RECT['x']) < 2 or abs(p['x'] - (RECT['x'] + RECT['width'])) < 2) and RECT['y'] <= p['y'] <= RECT['y'] + RECT['height']
    return on_horizontal or on_vertical

def is_on_circle_border(p):
    return abs(math.hypot(p['x'] - CIRCLE['cx'], p['y'] - CIRCLE['cy']) - CIRCLE['r']) < 2

def is_on_triangle_border(p):
    v = TRI['v']
    return dist_to_line_segment(p, v[0], v[1]) < 2 or \
           dist_to_line_segment(p, v[1], v[2]) < 2 or \
           dist_to_line_segment(p, v[2], v[0]) < 2
           
# --- 主要遊戲邏輯函式 ---

def generate_puzzle():
    st.session_state.placed_items = []
    st.session_state.correct_answers = {}
    st.session_state.current_theme = random.choice(EMOJI_THEMES)
    
    for zone in ZONE_DEFINITIONS:
        count = random.randint(1, 2)
        st.session_state.correct_answers[zone['type']] = count
        
        if 'border' in zone['type']:
            place_items_on_border(zone, count)
        else:
            place_items_inside_zone(zone, count)
    
    st.session_state.puzzle_generated = True

def place_items_inside_zone(zone, count):
    placed_count = 0
    for _ in range(500):
        if placed_count >= count: break
        
        p = {'x': random.uniform(0, CANVAS_W), 'y': random.uniform(0, CANVAS_H)}
        is_in_zone = get_zone_condition(zone['type'])(p)
        is_overlapping = any(((p['x'] - item['x'])**2 + (p['y'] - item['y'])**2) < MIN_DISTANCE_SQ for item in st.session_state.placed_items)

        if is_in_zone and not is_overlapping:
            st.session_state.placed_items.append({'x': p['x'], 'y': p['y'], 'emoji': st.session_state.current_theme['items'][zone['emoji_idx']]})
            placed_count += 1

def place_items_on_border(zone, count):
    for _ in range(count):
        for _ in range(200):
            p = get_point_on_border(zone['type'])
            is_inside_other_shape = False
            if zone['type'] == 'rect-border' and (is_inside_circle(p) or is_inside_triangle(p)): is_inside_other_shape = True
            if zone['type'] == 'circle-border' and (is_inside_rect(p) or is_inside_triangle(p)): is_inside_other_shape = True
            if zone['type'] == 'tri-border' and (is_inside_rect(p) or is_inside_circle(p)): is_inside_other_shape = True

            is_overlapping = any(((p['x'] - item['x'])**2 + (p['y'] - item['y'])**2) < MIN_DISTANCE_SQ for item in st.session_state.placed_items)

            if not is_inside_other_shape and not is_overlapping:
                st.session_state.placed_items.append({'x': p['x'], 'y': p['y'], 'emoji': st.session_state.current_theme['items'][zone['emoji_idx']]})
                break

def get_zone_condition(zone_type):
    conditions = {
        'rect-only': lambda p: is_inside_rect(p) and not is_inside_circle(p) and not is_inside_triangle(p),
        'circle-only': lambda p: not is_inside_rect(p) and is_inside_circle(p) and not is_inside_triangle(p),
        'tri-only': lambda p: not is_inside_rect(p) and not is_inside_circle(p) and is_inside_triangle(p),
        'rect-circle': lambda p: is_inside_rect(p) and is_inside_circle(p) and not is_inside_triangle(p),
        'rect-tri': lambda p: is_inside_rect(p) and not is_inside_circle(p) and is_inside_triangle(p),
        'circle-tri': lambda p: not is_inside_rect(p) and is_inside_circle(p) and is_inside_triangle(p),
        'all-three': lambda p: is_inside_rect(p) and is_inside_circle(p) and is_inside_triangle(p),
        'outside': lambda p: not is_inside_rect(p) and not is_inside_circle(p) and not is_inside_triangle(p)
    }
    return conditions[zone_type]

def get_point_on_border(border_type):
    t = random.random()
    if border_type == 'rect-border':
        perimeter = RECT['width'] * 2 + RECT['height'] * 2
        dist = t * perimeter
        if dist < RECT['width']: return {'x': RECT['x'] + dist, 'y': RECT['y']}
        dist -= RECT['width']
        if dist < RECT['height']: return {'x': RECT['x'] + RECT['width'], 'y': RECT['y'] + dist}
        dist -= RECT['height']
        if dist < RECT['width']: return {'x': RECT['x'] + RECT['width'] - dist, 'y': RECT['y'] + RECT['height']}
        dist -= RECT['width']
        return {'x': RECT['x'], 'y': RECT['y'] + RECT['height'] - dist}
    elif border_type == 'circle-border':
        angle = t * 2 * math.pi
        return {'x': CIRCLE['cx'] + CIRCLE['r'] * math.cos(angle), 'y': CIRCLE['cy'] + CIRCLE['r'] * math.sin(angle)}
    elif border_type == 'tri-border':
        v = TRI['v']
        lengths = [math.hypot(v[i]['x'] - v[(i-1)%3]['x'], v[i]['y'] - v[(i-1)%3]['y']) for i in range(3)]
        perimeter = sum(lengths)
        dist = t * perimeter
        if dist < lengths[0]:
            ratio = dist / lengths[0]
            return {'x': v[2]['x'] + ratio * (v[0]['x']-v[2]['x']), 'y': v[2]['y'] + ratio * (v[0]['y']-v[2]['y'])}
        dist -= lengths[0]
        if dist < lengths[1]:
            ratio = dist / lengths[1]
            return {'x': v[0]['x'] + ratio * (v[1]['x']-v[0]['x']), 'y': v[0]['y'] + ratio * (v[1]['y']-v[0]['y'])}
        dist -= lengths[1]
        ratio = dist / lengths[2]
        return {'x': v[1]['x'] + ratio * (v[2]['x']-v[1]['x']), 'y': v[1]['y'] + ratio * (v[2]['y']-v[1]['y'])}
    return {'x':0, 'y':0}


# --- Streamlit 網頁介面 (UI) ---
st.set_page_config(page_title="數圖形裡的物品", layout="wide")
st.title("數一數，有幾個？")
st.markdown("點擊 **產生新題目** 就可以開始挑戰囉！")

canvas_container = st.container()
questions_container = st.container()

col1, col2 = st.columns([1,1])
with col1:
    if st.button("產生新題目", use_container_width=True):
        generate_puzzle()
        st.session_state.feedback = None
        st.rerun()

with col2:
    if 'puzzle_generated' in st.session_state and st.session_state.puzzle_generated:
        if st.button("檢查答案", use_container_width=True, type="primary"):
            all_correct = True
            for zone in ZONE_DEFINITIONS:
                user_answer = st.session_state.get(f"answer_{zone['type']}", 0)
                correct_answer = st.session_state.correct_answers.get(zone['type'], 0)
                if user_answer != correct_answer:
                    all_correct = False
                    break
            
            if all_correct:
                st.session_state.feedback = ("success", "全部答對了，你太厲害了！🎉")
            else:
                st.session_state.feedback = ("error", "不對喔，再仔細數一次看看！🤔")
            st.rerun()

if 'feedback' in st.session_state and st.session_state.feedback:
    msg_type, msg_text = st.session_state.feedback
    if msg_type == "success":
        st.success(msg_text)
    else:
        st.error(msg_text)

if 'puzzle_generated' in st.session_state and st.session_state.puzzle_generated:
    with canvas_container:
        items_html = ""
        for item in st.session_state.placed_items:
            items_html += f'<div style="position: absolute; left: {item["x"] - ITEM_SIZE/2}px; top: {item["y"] - ITEM_SIZE/2}px; font-size: 1.75rem; width: {ITEM_SIZE}px; height: {ITEM_SIZE}px; display: flex; align-items: center; justify-content: center;">{item["emoji"]}</div>'
        
        canvas_html = f"""
        <div style="position: relative; width:{CANVAS_W}px; height:{CANVAS_H}px; background-color: #f8fafc; border-radius: 1rem; border: 2px solid #e2e8f0; margin: auto;">
            <div style="position: absolute; left: {RECT['x']}px; top: {RECT['y']}px; width: {RECT['width']}px; height: {RECT['height']}px; border: 4px solid #f59e0b; border-radius: 0.5rem;"></div>
            <div style="position: absolute; left: {CIRCLE['cx']-CIRCLE['r']}px; top: {CIRCLE['cy']-CIRCLE['r']}px; width: {CIRCLE['r']*2}px; height: {CIRCLE['r']*2}px; border: 4px solid #14b8a6; border-radius: 9999px;"></div>
            <svg style="position: absolute; width:100%; height:100%; top:0; left:0; overflow:visible;">
                <polygon points="{TRI['v'][0]['x']},{TRI['v'][0]['y']} {TRI['v'][1]['x']},{TRI['v'][1]['y']} {TRI['v'][2]['x']},{TRI['v'][2]['y']}" style="fill:transparent; stroke:#f43f5e; stroke-width:4;" />
            </svg>
            {items_html}
        </div>
        """
        st.markdown(canvas_html, unsafe_allow_html=True)

    with questions_container:
        # 將問題分成三欄顯示
        q_cols = st.columns(3)
        col_idx = 0
        # 將問題排序以獲得一致的顯示順序
        sorted_zones = sorted(ZONE_DEFINITIONS, key=lambda x: x['name'])
        for zone in sorted_zones:
            # 只有當該區域有物品時，才顯示問題
            if st.session_state.correct_answers.get(zone['type'], 0) > 0:
                with q_cols[col_idx % 3]:
                    # 建立一個容器來美化每個問題
                    with st.container(border=True):
                        # 為每個問題建立左右兩欄
                        label_col, input_col = st.columns([3, 2])
                        with label_col:
                            # 用 markdown 顯示問題，可以控制樣式
                            st.markdown(f"<p style='font-size: 1.1rem; text-align: right; margin-top: 10px;'>{zone['name']}有幾個 {st.session_state.current_theme['items'][zone['emoji_idx']]}？</p>", unsafe_allow_html=True)
                        with input_col:
                            # 數字輸入框，隱藏它自己的標籤
                            st.number_input(
                                label=f"hidden_label_for_{zone['type']}", # label 還是需要，但設為隱藏
                                min_value=0, 
                                step=1, 
                                key=f"answer_{zone['type']}",
                                label_visibility="collapsed"
                            )
                col_idx += 1
