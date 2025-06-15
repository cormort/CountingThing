import streamlit as st
import random
import math

# --- 遊戲設定 (Configuration) ---

# 定義所有可用的Emoji主題 (已新增臉部表情)
EMOJI_THEMES = [
    { "name": "動物", "items": ['🐶', '🐱', '🐭', '🦊', '🐻', '🐼', '🐨', '🐯', '🐰', '🐷', '🐸', '🐵'] },
    { "name": "恐龍", "items": ['🦖', '🦕', '🐊', '🐉', '🐲', '🦎', '🐍', '🐢', '🦤', '🦚', '🦢', '🦜'] },
    { "name": "食物", "items": ['🍎', '🍌', '🍉', '🍇', '🍓', '🍒', ' ', '🍍', '🥝', '🍔', '🍕', '🍩'] },
    { "name": "表情", "items": ['😄', '😠', '😢', '😂', '😮', '🤔', '😴', '😎', '😍', '😭', '😉', '😐'] },
]

# 定義每個區域的名稱和對應的Emoji索引
# 這會讓程式更有彈性，例如 'rect-only' 區域將永遠使用主題中的第0個emoji
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
# 這些數值定義了畫布上三個固定圖形的位置和大小
CANVAS_W, CANVAS_H = 900, 400
RECT = { "x": 50, "y": 120, "width": 400, "height": 220 }
CIRCLE = { "cx": 650, "cy": 230, "r": 120 }
TRI = { "v": [ {"x": 250, "y": 50}, {"x": 750, "y": 50}, {"x": 500, "y": 300} ] }
ITEM_SIZE = 40
MIN_DISTANCE_SQ = 45 * 45  # 用於判斷重疊的最小距離的平方

# --- 幾何判斷輔助函式 (Geometric Helper Functions) ---
# 這些函式用來判斷一個點(x,y)是在圖形的裡面還是邊上

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

# 產生一個新的謎題
def generate_puzzle():
    # 在 st.session_state 中初始化或重置遊戲狀態
    st.session_state.placed_items = []
    st.session_state.correct_answers = {}
    st.session_state.current_theme = random.choice(EMOJI_THEMES)
    
    # 為每個區域隨機產生1到2個物品
    for zone in ZONE_DEFINITIONS:
        count = random.randint(1, 2)
        st.session_state.correct_answers[zone['type']] = count
        
        # 根據區域類型，呼叫不同的放置函式
        if 'border' in zone['type']:
            place_items_on_border(zone, count)
        else:
            place_items_inside_zone(zone, count)
    
    # 標示謎題已產生，可以顯示題目了
    st.session_state.puzzle_generated = True

# 在特定區域「裡面」隨機放置物品
def place_items_inside_zone(zone, count):
    placed_count = 0
    # 最多嘗試500次，以防找不到不重疊的位置
    for _ in range(500):
        if placed_count >= count: break
        
        # 隨機產生一個座標點
        p = {'x': random.uniform(0, CANVAS_W), 'y': random.uniform(0, CANVAS_H)}

        # 檢查這個點是否符合該區域的條件 (例如，只在圓形內)
        is_in_zone = get_zone_condition(zone['type'])(p)
        
        # 檢查是否與已放置的物品重疊
        is_overlapping = any(((p['x'] - item['x'])**2 + (p['y'] - item['y'])**2) < MIN_DISTANCE_SQ for item in st.session_state.placed_items)

        if is_in_zone and not is_overlapping:
            # 如果條件都符合，就將物品資訊存起來
            st.session_state.placed_items.append({'x': p['x'], 'y': p['y'], 'emoji': st.session_state.current_theme['items'][zone['emoji_idx']]})
            placed_count += 1

# 在特定圖形的「邊上」精準放置物品
def place_items_on_border(zone, count):
    for _ in range(count):
        # 最多嘗試200次，以防找不到不重疊的位置
        for _ in range(200):
            # 隨機選一個邊上的點
            p = get_point_on_border(zone['type'])

            # 確保邊上的點不在任何其他圖形的"裡面"，避免混淆
            is_inside_other_shape = False
            if zone['type'] == 'rect-border' and (is_inside_circle(p) or is_inside_triangle(p)): is_inside_other_shape = True
            if zone['type'] == 'circle-border' and (is_inside_rect(p) or is_inside_triangle(p)): is_inside_other_shape = True
            if zone['type'] == 'tri-border' and (is_inside_rect(p) or is_inside_circle(p)): is_inside_other_shape = True

            is_overlapping = any(((p['x'] - item['x'])**2 + (p['y'] - item['y'])**2) < MIN_DISTANCE_SQ for item in st.session_state.placed_items)

            if not is_inside_other_shape and not is_overlapping:
                st.session_state.placed_items.append({'x': p['x'], 'y': p['y'], 'emoji': st.session_state.current_theme['items'][zone['emoji_idx']]})
                break

# 根據區域類型返回對應的判斷函式
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

# 根據圖形類型，隨機在邊上取一個點
def get_point_on_border(border_type):
    t = random.random() # 0到1之間的隨機數，代表在邊上的相對位置
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

# 建立一個容器來放畫布，這樣比較好控制
canvas_container = st.container()

# 建立一個多欄位的容器來放問題
questions_container = st.container()

# 建立一個多欄位的容器來放按鈕
col1, col2 = st.columns([1,1])
with col1:
    if st.button("產生新題目", use_container_width=True):
        generate_puzzle()
        st.session_state.feedback = None # 清除舊的回饋
        st.rerun() # 重新整理頁面以更新題目

with col2:
    # 只有在謎題產生後才顯示檢查按鈕
    if 'puzzle_generated' in st.session_state and st.session_state.puzzle_generated:
        if st.button("檢查答案", use_container_width=True, type="primary"):
            all_correct = True
            # 遍歷所有問題類型，檢查答案
            for zone in ZONE_DEFINITIONS:
                user_answer = st.session_state.get(f"answer_{zone['type']}", 0)
                correct_answer = st.session_state.correct_answers.get(zone['type'], 0)
                if user_answer != correct_answer:
                    all_correct = False
                    break
            
            # 根據結果設定回饋訊息
            if all_correct:
                st.session_state.feedback = ("success", "全部答對了，你太厲害了！🎉")
            else:
                st.session_state.feedback = ("error", "不對喔，再仔細數一次看看！🤔")
            st.rerun()

# 顯示回饋訊息
if 'feedback' in st.session_state and st.session_state.feedback:
    msg_type, msg_text = st.session_state.feedback
    if msg_type == "success":
        st.success(msg_text)
    else:
        st.error(msg_text)

# 如果謎題已產生，就開始繪製所有東西
if 'puzzle_generated' in st.session_state and st.session_state.puzzle_generated:
    # --- 繪製畫布和物品 ---
    with canvas_container:
        # 使用 st.markdown 和 HTML/SVG 來繪製圖形和絕對定位的物品
        # 這是 Streamlit 中實現複雜2D佈局的常用技巧
        items_html = ""
        for item in st.session_state.placed_items:
            # 將每個物品的位置和emoji組合成一個HTML元素
            items_html += f'<div class="item-box" style="left: {item["x"]-ITEM_SIZE/2}px; top: {item["y"]-ITEM_SIZE/2}px;">{item["emoji"]}</div>'
        
        # 將所有圖形和物品組合成一個大的HTML字串
        canvas_html = f"""
        <div style="position: relative; width:{CANVAS_W}px; height:{CANVAS_H}px; background-color: #f8fafc; border-radius: 1rem; border: 2px solid #e2e8f0;">
            <div style="position: absolute; left: {RECT['x']}px; top: {RECT['y']}px; width: {RECT['width']}px; height: {RECT['height']}px; border: 4px solid #f59e0b; border-radius: 0.5rem;"></div>
            <div style="position: absolute; left: {CIRCLE['cx']-CIRCLE['r']}px; top: {CIRCLE['cy']-CIRCLE['r']}px; width: {CIRCLE['r']*2}px; height: {CIRCLE['r']*2}px; border: 4px solid #14b8a6; border-radius: 9999px;"></div>
            <svg style="position: absolute; width:100%; height:100%; top:0; left:0; overflow:visible;">
                <polygon points="{TRI['v'][0]['x']},{TRI['v'][0]['y']} {TRI['v'][1]['x']},{TRI['v'][1]['y']} {TRI['v'][2]['x']},{TRI['v'][2]['y']}" style="fill:transparent; stroke:#f43f5e; stroke-width:4;" />
            </svg>
            {items_html}
        </div>
        """
        # 使用 st.markdown 顯示整個畫布
        st.markdown(canvas_html, unsafe_allow_html=True)

    # --- 顯示問題輸入框 ---
    with questions_container:
        # 將問題分成三欄顯示
        q_cols = st.columns(3)
        col_idx = 0
        for zone in ZONE_DEFINITIONS:
            # 只有當該區域有物品時，才顯示問題
            if st.session_state.correct_answers.get(zone['type'], 0) > 0:
                with q_cols[col_idx % 3]:
                    # 建立每個問題的數字輸入框
                    st.number_input(
                        label=f"{zone['name']}有幾個 {st.session_state.current_theme['items'][zone['emoji_idx']]}？", 
                        min_value=0, 
                        step=1, 
                        key=f"answer_{zone['type']}"
                    )
                col_idx += 1

 