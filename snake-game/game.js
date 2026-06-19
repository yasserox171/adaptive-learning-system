const GRID = 20;
const CELL = 16; // canvas = 320x320
const BASE_SPEED = 200;
const SPEED_STEP = 15;
const FOODS_PER_LEVEL = 5;
const MAX_LEVEL = 10;

const COLORS = {
  bg: '#0d1117',
  grid: '#161b22',
  food: '#ff4757',
  foodShine: '#ff6b81',
  head: '#22c55e',
  body: '#4ade80',
  bodyDark: '#16a34a',
  eyes: '#fff',
};

const canvas = document.getElementById('game');
const ctx = canvas.getContext('2d');
canvas.width = GRID * CELL;
canvas.height = GRID * CELL;

// DOM refs
const scoreEl = document.getElementById('score');
const levelEl = document.getElementById('level');
const highEl = document.getElementById('high');
const overlay = document.getElementById('overlay');
const overlayTitle = document.getElementById('overlay-title');
const overlayMsg = document.getElementById('overlay-msg');
const retryBtn = document.getElementById('retry-btn');
const pauseBtn = document.getElementById('pause-btn');
const canvasWrap = document.getElementById('canvas-wrap');

let state = {};
let rafId = null;
let lastTick = 0;

function initState() {
  const mid = Math.floor(GRID / 2);
  return {
    snake: [
      { x: mid, y: mid },
      { x: mid - 1, y: mid },
      { x: mid - 2, y: mid },
    ],
    dir: { x: 1, y: 0 },
    nextDir: { x: 1, y: 0 },
    food: null,
    score: 0,
    level: 1,
    foodEaten: 0,
    highScore: parseInt(localStorage.getItem('snakeHigh') || '0'),
    status: 'idle',
  };
}

function placeFood() {
  const occupied = new Set(state.snake.map(s => `${s.x},${s.y}`));
  let f;
  do {
    f = { x: Math.floor(Math.random() * GRID), y: Math.floor(Math.random() * GRID) };
  } while (occupied.has(`${f.x},${f.y}`));
  state.food = f;
}

function tickInterval() {
  return Math.max(60, BASE_SPEED - (state.level - 1) * SPEED_STEP);
}

function startGame() {
  cancelAnimationFrame(rafId);
  state = initState();
  placeFood();
  state.status = 'running';
  overlay.classList.add('hidden');
  updateHUD();
  lastTick = performance.now();
  rafId = requestAnimationFrame(loop);
}

function togglePause() {
  if (state.status === 'running') {
    state.status = 'paused';
    pauseBtn.textContent = '▶ استئناف';
    overlayTitle.textContent = '⏸ متوقف';
    overlayMsg.textContent = 'اضغط استئناف للمتابعة';
    retryBtn.style.display = 'none';
    overlay.classList.remove('hidden');
  } else if (state.status === 'paused') {
    state.status = 'running';
    pauseBtn.textContent = '⏸ إيقاف';
    overlay.classList.add('hidden');
    retryBtn.style.display = '';
    lastTick = performance.now();
    rafId = requestAnimationFrame(loop);
  }
}

function gameOver() {
  state.status = 'dead';
  cancelAnimationFrame(rafId);
  if (state.score > state.highScore) {
    state.highScore = state.score;
    localStorage.setItem('snakeHigh', state.highScore);
  }
  updateHUD();
  overlayTitle.textContent = '💀 انتهت اللعبة!';
  overlayMsg.textContent = `النقاط: ${state.score} | المستوى: ${state.level}`;
  retryBtn.style.display = '';
  pauseBtn.textContent = '⏸ إيقاف';
  overlay.classList.remove('hidden');
}

function setDir(dx, dy) {
  if (state.status !== 'running') return;
  if (dx === -state.dir.x && dy === -state.dir.y) return; // no 180°
  state.nextDir = { x: dx, y: dy };
}

function loop(ts) {
  if (state.status !== 'running') return;
  rafId = requestAnimationFrame(loop);
  if (ts - lastTick < tickInterval()) return;
  lastTick = ts;
  tick();
}

function tick() {
  state.dir = state.nextDir;
  const head = state.snake[0];
  const newHead = { x: head.x + state.dir.x, y: head.y + state.dir.y };

  // wall collision
  if (newHead.x < 0 || newHead.x >= GRID || newHead.y < 0 || newHead.y >= GRID) {
    return gameOver();
  }
  // self collision
  if (state.snake.some(s => s.x === newHead.x && s.y === newHead.y)) {
    return gameOver();
  }

  state.snake.unshift(newHead);

  if (newHead.x === state.food.x && newHead.y === state.food.y) {
    // ate food
    state.score += state.level * 10;
    state.foodEaten++;
    const newLevel = Math.min(Math.ceil(state.foodEaten / FOODS_PER_LEVEL), MAX_LEVEL);
    if (newLevel > state.level) {
      state.level = newLevel;
      flashLevelUp();
    }
    placeFood();
  } else {
    state.snake.pop();
  }

  updateHUD();
  draw();
}

function flashLevelUp() {
  canvasWrap.classList.remove('level-up');
  void canvasWrap.offsetWidth; // reflow to restart animation
  canvasWrap.classList.add('level-up');
  setTimeout(() => canvasWrap.classList.remove('level-up'), 400);
}

function updateHUD() {
  scoreEl.textContent = `نقاط: ${state.score}`;
  levelEl.textContent = `مستوى: ${state.level}`;
  highEl.textContent = `أعلى: ${state.highScore}`;
}

function draw() {
  // background
  ctx.fillStyle = COLORS.bg;
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  // grid lines
  ctx.strokeStyle = COLORS.grid;
  ctx.lineWidth = 0.5;
  for (let i = 0; i <= GRID; i++) {
    ctx.beginPath();
    ctx.moveTo(i * CELL, 0);
    ctx.lineTo(i * CELL, canvas.height);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(0, i * CELL);
    ctx.lineTo(canvas.width, i * CELL);
    ctx.stroke();
  }

  // food
  if (state.food) {
    const fx = state.food.x * CELL;
    const fy = state.food.y * CELL;
    ctx.fillStyle = COLORS.food;
    ctx.beginPath();
    ctx.roundRect(fx + 2, fy + 2, CELL - 4, CELL - 4, 3);
    ctx.fill();
    // shine
    ctx.fillStyle = COLORS.foodShine;
    ctx.fillRect(fx + 4, fy + 4, 3, 3);
  }

  // snake body (reverse so head is on top)
  for (let i = state.snake.length - 1; i >= 0; i--) {
    const seg = state.snake[i];
    const x = seg.x * CELL;
    const y = seg.y * CELL;
    const isHead = i === 0;

    ctx.fillStyle = isHead ? COLORS.head : (i % 2 === 0 ? COLORS.body : COLORS.bodyDark);
    ctx.beginPath();
    ctx.roundRect(x + 1, y + 1, CELL - 2, CELL - 2, isHead ? 4 : 2);
    ctx.fill();

    // eyes on head
    if (isHead) {
      ctx.fillStyle = COLORS.eyes;
      const d = state.dir;
      let e1, e2;
      if (d.x === 1)  { e1 = [x+10, y+3];  e2 = [x+10, y+9]; }
      else if (d.x === -1) { e1 = [x+2, y+3];  e2 = [x+2, y+9]; }
      else if (d.y === -1) { e1 = [x+3, y+2];  e2 = [x+9, y+2]; }
      else               { e1 = [x+3, y+10]; e2 = [x+9, y+10]; }
      ctx.fillRect(e1[0], e1[1], 3, 3);
      ctx.fillRect(e2[0], e2[1], 3, 3);
    }
  }
}

// ── Keyboard ──
document.addEventListener('keydown', e => {
  if (state.status === 'idle') { startGame(); return; }
  switch (e.key) {
    case 'ArrowUp':    case 'w': e.preventDefault(); setDir(0, -1); break;
    case 'ArrowDown':  case 's': e.preventDefault(); setDir(0, 1);  break;
    case 'ArrowLeft':  case 'a': e.preventDefault(); setDir(-1, 0); break;
    case 'ArrowRight': case 'd': e.preventDefault(); setDir(1, 0);  break;
    case ' ':                    e.preventDefault(); togglePause(); break;
  }
});

// ── D-pad buttons ──
document.getElementById('btn-up').addEventListener('touchstart', e => { e.preventDefault(); setDir(0, -1); }, { passive: false });
document.getElementById('btn-down').addEventListener('touchstart', e => { e.preventDefault(); setDir(0, 1); }, { passive: false });
document.getElementById('btn-left').addEventListener('touchstart', e => { e.preventDefault(); setDir(1, 0); }, { passive: false });
document.getElementById('btn-right').addEventListener('touchstart', e => { e.preventDefault(); setDir(-1, 0); }, { passive: false });
// fallback click for desktop
document.getElementById('btn-up').addEventListener('click', () => setDir(0, -1));
document.getElementById('btn-down').addEventListener('click', () => setDir(0, 1));
document.getElementById('btn-left').addEventListener('click', () => setDir(1, 0));
document.getElementById('btn-right').addEventListener('click', () => setDir(-1, 0));

// ── Swipe on canvas ──
let swipeX = 0, swipeY = 0;
canvas.addEventListener('touchstart', e => {
  e.preventDefault();
  swipeX = e.changedTouches[0].clientX;
  swipeY = e.changedTouches[0].clientY;
}, { passive: false });

canvas.addEventListener('touchend', e => {
  e.preventDefault();
  const dx = e.changedTouches[0].clientX - swipeX;
  const dy = e.changedTouches[0].clientY - swipeY;
  if (Math.abs(dx) < 20 && Math.abs(dy) < 20) return;
  if (Math.abs(dx) > Math.abs(dy)) setDir(dx > 0 ? -1 : 1, 0);
  else setDir(0, dy > 0 ? 1 : -1);
}, { passive: false });

// ── Action buttons ──
retryBtn.addEventListener('click', startGame);
retryBtn.addEventListener('touchstart', e => { e.preventDefault(); startGame(); }, { passive: false });
pauseBtn.addEventListener('click', togglePause);
pauseBtn.addEventListener('touchstart', e => { e.preventDefault(); togglePause(); }, { passive: false });

// ── Init ──
state = initState();
updateHUD();
draw();
