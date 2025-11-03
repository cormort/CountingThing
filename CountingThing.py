import React, { useState, useEffect } from 'react';
import { RefreshCw, CheckCircle2, AlertCircle, Trophy, Sparkles } from 'lucide-react';

// 遊戲設定
const EMOJI_THEMES = [
  { name: "動物", items: ['🐶', '🐱', '🐭', '🦊', '🐻', '🐼', '🐨', '🐯', '🐰', '🐷', '🐸', '🐵'] },
  { name: "恐龍", items: ['🦖', '🦕', '🐊', '🐉', '🐲', '🦎', '🐍', '🐢', '🦤', '🦚', '🦢', '🦜'] },
  { name: "食物", items: ['🍎', '🍌', '🍉', '🍇', '🍓', '🍒', '🍑', '🍍', '🥝', '🍔', '🍕', '🍩'] },
  { name: "表情", items: ['😄', '😠', '😢', '😂', '😮', '🤔', '😴', '😎', '😍', '😭', '😉', '😐'] },
];

const ZONE_DEFINITIONS = [
  { name: '在長方形裡面', type: 'rect-only', emoji_idx: 0 },
  { name: '在圓形裡面', type: 'circle-only', emoji_idx: 1 },
  { name: '在三角形裡面', type: 'tri-only', emoji_idx: 2 },
  { name: '在長方形和圓形裡面', type: 'rect-circle', emoji_idx: 3 },
  { name: '在長方形和三角形裡面', type: 'rect-tri', emoji_idx: 4 },
  { name: '在圓形和三角形裡面', type: 'circle-tri', emoji_idx: 5 },
  { name: '在三個圖形裡面', type: 'all-three', emoji_idx: 6 },
  { name: '在所有圖形外面', type: 'outside', emoji_idx: 7 },
  { name: '在長方形邊上', type: 'rect-border', emoji_idx: 8 },
  { name: '在圓形邊上', type: 'circle-border', emoji_idx: 9 },
  { name: '在三角形邊上', type: 'tri-border', emoji_idx: 10 },
];

const CANVAS_W = 900, CANVAS_H = 400;
const RECT = { x: 50, y: 120, width: 400, height: 220 };
const CIRCLE = { cx: 650, cy: 230, r: 120 };
const TRI = { v: [{ x: 250, y: 50 }, { x: 750, y: 50 }, { x: 500, y: 300 }] };
const ITEM_SIZE = 40;
const MIN_DISTANCE_SQ = 45 * 45;

// 幾何判斷函式
const isInsideRect = (p) => 
  RECT.x <= p.x && p.x <= RECT.x + RECT.width && RECT.y <= p.y && p.y <= RECT.y + RECT.height;

const isInsideCircle = (p) => 
  Math.hypot(p.x - CIRCLE.cx, p.y - CIRCLE.cy) <= CIRCLE.r;

const isInsideTriangle = (p) => {
  const sign = (p1, p2, p3) => (p1.x - p3.x) * (p2.y - p3.y) - (p2.x - p3.x) * (p1.y - p3.y);
  const d1 = sign(p, TRI.v[0], TRI.v[1]);
  const d2 = sign(p, TRI.v[1], TRI.v[2]);
  const d3 = sign(p, TRI.v[2], TRI.v[0]);
  const hasNeg = (d1 < 0) || (d2 < 0) || (d3 < 0);
  const hasPos = (d1 > 0) || (d2 > 0) || (d3 > 0);
  return !(hasNeg && hasPos);
};

const getZoneCondition = (type) => {
  const conditions = {
    'rect-only': (p) => isInsideRect(p) && !isInsideCircle(p) && !isInsideTriangle(p),
    'circle-only': (p) => !isInsideRect(p) && isInsideCircle(p) && !isInsideTriangle(p),
    'tri-only': (p) => !isInsideRect(p) && !isInsideCircle(p) && isInsideTriangle(p),
    'rect-circle': (p) => isInsideRect(p) && isInsideCircle(p) && !isInsideTriangle(p),
    'rect-tri': (p) => isInsideRect(p) && !isInsideCircle(p) && isInsideTriangle(p),
    'circle-tri': (p) => !isInsideRect(p) && isInsideCircle(p) && isInsideTriangle(p),
    'all-three': (p) => isInsideRect(p) && isInsideCircle(p) && isInsideTriangle(p),
    'outside': (p) => !isInsideRect(p) && !isInsideCircle(p) && !isInsideTriangle(p)
  };
  return conditions[type];
};

const generatePuzzle = () => {
  const placedItems = [];
  const correctAnswers = {};
  const currentTheme = EMOJI_THEMES[Math.floor(Math.random() * EMOJI_THEMES.length)];
  
  ZONE_DEFINITIONS.forEach(zone => {
    const count = Math.floor(Math.random() * 2) + 1;
    correctAnswers[zone.type] = count;
    
    // Skip border zones for simplicity
    if (zone.type.includes('border')) {
      return;
    }
    
    let placed = 0;
    const condition = getZoneCondition(zone.type);
    
    for (let attempt = 0; attempt < 500 && placed < count; attempt++) {
      const p = { x: Math.random() * CANVAS_W, y: Math.random() * CANVAS_H };
      const isInZone = condition(p);
      const isOverlapping = placedItems.some(item => 
        Math.pow(p.x - item.x, 2) + Math.pow(p.y - item.y, 2) < MIN_DISTANCE_SQ
      );
      
      if (isInZone && !isOverlapping) {
        placedItems.push({ x: p.x, y: p.y, emoji: currentTheme.items[zone.emoji_idx] });
        placed++;
      }
    }
  });
  
  return { placedItems, correctAnswers, currentTheme };
};

export default function ShapeCountingGame() {
  const [gameState, setGameState] = useState(null);
  const [answers, setAnswers] = useState({});
  const [feedback, setFeedback] = useState(null);
  const [score, setScore] = useState(0);

  const newPuzzle = () => {
    setGameState(generatePuzzle());
    setAnswers({});
    setFeedback(null);
  };

  useEffect(() => {
    newPuzzle();
  }, []);

  const checkAnswers = () => {
    if (!gameState) return;
    
    let correct = 0;
    let total = 0;
    
    Object.keys(gameState.correctAnswers).forEach(type => {
      if (gameState.correctAnswers[type] > 0) {
        total++;
        if (answers[type] === gameState.correctAnswers[type]) {
          correct++;
        }
      }
    });
    
    if (correct === total) {
      setFeedback({ type: 'success', message: '🎉 太棒了！全部答對！' });
      setScore(prev => prev + 1);
    } else {
      setFeedback({ type: 'error', message: `😅 答對了 ${correct}/${total} 題，再試試看！` });
    }
  };

  if (!gameState) return <div className="flex items-center justify-center h-screen">載入中...</div>;

  const activeZones = ZONE_DEFINITIONS.filter(zone => gameState.correctAnswers[zone.type] > 0);

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-blue-50 to-pink-50 p-8">
      <div className="max-w-7xl mx-auto">
        {/* 標題區 */}
        <div className="text-center mb-8 space-y-2">
          <div className="flex items-center justify-center gap-3 mb-3">
            <Sparkles className="text-yellow-500 w-8 h-8" />
            <h1 className="text-5xl font-black bg-gradient-to-r from-purple-600 via-pink-600 to-blue-600 bg-clip-text text-transparent">
              數一數，有幾個？
            </h1>
            <Sparkles className="text-yellow-500 w-8 h-8" />
          </div>
          <p className="text-xl text-gray-600">當前主題：<span className="font-bold text-purple-600">{gameState.currentTheme.name}</span></p>
          <div className="flex items-center justify-center gap-2 text-lg">
            <Trophy className="text-yellow-600 w-6 h-6" />
            <span className="font-bold text-gray-700">得分：{score}</span>
          </div>
        </div>

        {/* 遊戲畫布 */}
        <div className="bg-white rounded-3xl shadow-2xl p-8 mb-8 border-4 border-purple-200">
          <div 
            className="relative mx-auto rounded-2xl shadow-inner"
            style={{ 
              width: CANVAS_W, 
              height: CANVAS_H,
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            }}
          >
            {/* 長方形 */}
            <div
              className="absolute border-8 border-amber-400 rounded-xl bg-amber-400/10 shadow-lg"
              style={{
                left: RECT.x,
                top: RECT.y,
                width: RECT.width,
                height: RECT.height,
              }}
            />
            
            {/* 圓形 */}
            <div
              className="absolute border-8 border-green-400 rounded-full bg-green-400/10 shadow-lg"
              style={{
                left: CIRCLE.cx - CIRCLE.r,
                top: CIRCLE.cy - CIRCLE.r,
                width: CIRCLE.r * 2,
                height: CIRCLE.r * 2,
              }}
            />
            
            {/* 三角形 */}
            <svg className="absolute inset-0 w-full h-full overflow-visible pointer-events-none">
              <defs>
                <filter id="glow">
                  <feGaussianBlur stdDeviation="2" result="coloredBlur"/>
                  <feMerge>
                    <feMergeNode in="coloredBlur"/>
                    <feMergeNode in="SourceGraphic"/>
                  </feMerge>
                </filter>
              </defs>
              <polygon
                points={`${TRI.v[0].x},${TRI.v[0].y} ${TRI.v[1].x},${TRI.v[1].y} ${TRI.v[2].x},${TRI.v[2].y}`}
                className="fill-rose-400/10 stroke-rose-400"
                strokeWidth="8"
                filter="url(#glow)"
              />
            </svg>
            
            {/* Emoji物品 */}
            {gameState.placedItems.map((item, idx) => (
              <div
                key={idx}
                className="absolute text-4xl transition-transform hover:scale-125 cursor-pointer animate-bounce"
                style={{
                  left: item.x - ITEM_SIZE / 2,
                  top: item.y - ITEM_SIZE / 2,
                  width: ITEM_SIZE,
                  height: ITEM_SIZE,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  animationDelay: `${idx * 0.1}s`,
                  animationDuration: '2s',
                }}
              >
                {item.emoji}
              </div>
            ))}
          </div>
        </div>

        {/* 反饋訊息 */}
        {feedback && (
          <div className={`mb-6 p-6 rounded-2xl shadow-lg flex items-center gap-4 text-lg font-bold ${
            feedback.type === 'success' 
              ? 'bg-gradient-to-r from-green-400 to-emerald-500 text-white' 
              : 'bg-gradient-to-r from-orange-400 to-pink-500 text-white'
          }`}>
            {feedback.type === 'success' ? <CheckCircle2 className="w-8 h-8" /> : <AlertCircle className="w-8 h-8" />}
            <span>{feedback.message}</span>
          </div>
        )}

        {/* 問題區 */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          {activeZones.map(zone => (
            <div 
              key={zone.type}
              className="bg-white rounded-2xl shadow-xl p-6 border-2 border-purple-200 hover:border-purple-400 transition-all hover:shadow-2xl transform hover:-translate-y-1"
            >
              <div className="flex items-center justify-between gap-4">
                <label className="text-lg font-bold text-gray-700 flex-1">
                  {zone.name}有幾個 <span className="text-3xl">{gameState.currentTheme.items[zone.emoji_idx]}</span> ？
                </label>
                <input
                  type="number"
                  min="0"
                  className="w-24 px-4 py-3 text-2xl font-bold text-center border-4 border-purple-300 rounded-xl focus:outline-none focus:ring-4 focus:ring-purple-400 focus:border-purple-500 bg-purple-50"
                  value={answers[zone.type] || ''}
                  onChange={(e) => setAnswers({ ...answers, [zone.type]: parseInt(e.target.value) || 0 })}
                />
              </div>
            </div>
          ))}
        </div>

        {/* 按鈕區 */}
        <div className="flex gap-4 justify-center">
          <button
            onClick={newPuzzle}
            className="flex items-center gap-3 px-8 py-4 bg-gradient-to-r from-blue-500 to-purple-600 text-white text-xl font-bold rounded-2xl shadow-lg hover:shadow-2xl transform hover:scale-105 transition-all"
          >
            <RefreshCw className="w-6 h-6" />
            產生新題目
          </button>
          <button
            onClick={checkAnswers}
            className="flex items-center gap-3 px-8 py-4 bg-gradient-to-r from-green-500 to-emerald-600 text-white text-xl font-bold rounded-2xl shadow-lg hover:shadow-2xl transform hover:scale-105 transition-all"
          >
            <CheckCircle2 className="w-6 h-6" />
            檢查答案
          </button>
        </div>
      </div>
    </div>
  );
}
