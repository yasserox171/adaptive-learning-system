import 'dart:async';
import 'dart:math';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  SystemChrome.setPreferredOrientations([DeviceOrientation.portraitUp]);
  runApp(const SnakeApp());
}

class SnakeApp extends StatelessWidget {
  const SnakeApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Snake Classic',
      debugShowCheckedModeBanner: false,
      theme: ThemeData.dark().copyWith(
        scaffoldBackgroundColor: const Color(0xFF1a1a2e),
      ),
      home: const SnakeGame(),
    );
  }
}

const int kGrid = 20;
const int kBaseSpeed = 200;
const int kSpeedStep = 15;
const int kFoodsPerLevel = 5;
const int kMaxLevel = 10;

const Color kBgColor    = Color(0xFF0d1117);
const Color kGridColor  = Color(0xFF161b22);
const Color kHeadColor  = Color(0xFF22c55e);
const Color kBodyColor  = Color(0xFF4ade80);
const Color kBodyDark   = Color(0xFF16a34a);
const Color kFoodColor  = Color(0xFFff4757);
const Color kAccent     = Color(0xFF4ade80);

class Pt {
  final int x, y;
  const Pt(this.x, this.y);

  @override
  bool operator ==(Object o) => o is Pt && o.x == x && o.y == y;

  @override
  int get hashCode => Object.hash(x, y);
}

enum Dir { up, down, left, right }

class SnakeGame extends StatefulWidget {
  const SnakeGame({super.key});

  @override
  State<SnakeGame> createState() => _SnakeGameState();
}

class _SnakeGameState extends State<SnakeGame> {
  List<Pt> _snake = [];
  Pt _food = const Pt(5, 5);
  Dir _dir = Dir.right;
  Dir _nextDir = Dir.right;
  int _score = 0;
  int _level = 1;
  int _foodEaten = 0;
  int _highScore = 0;
  String _status = 'idle';
  Timer? _timer;
  final _rand = Random();

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  void _start() {
    _timer?.cancel();
    final m = kGrid ~/ 2;
    setState(() {
      _snake = [Pt(m, m), Pt(m - 1, m), Pt(m - 2, m)];
      _dir = Dir.right;
      _nextDir = Dir.right;
      _score = 0;
      _level = 1;
      _foodEaten = 0;
      _status = 'running';
    });
    _placeFood();
    _resetTimer();
  }

  void _resetTimer() {
    _timer?.cancel();
    final ms = max(60, kBaseSpeed - (_level - 1) * kSpeedStep);
    _timer = Timer.periodic(Duration(milliseconds: ms), (_) => _tick());
  }

  void _placeFood() {
    final occ = _snake.toSet();
    Pt p;
    do { p = Pt(_rand.nextInt(kGrid), _rand.nextInt(kGrid)); } while (occ.contains(p));
    setState(() => _food = p);
  }

  void _tick() {
    if (_status != 'running') return;
    _dir = _nextDir;
    final h = _snake.first;

    final nh = switch (_dir) {
      Dir.up    => Pt(h.x, h.y - 1),
      Dir.down  => Pt(h.x, h.y + 1),
      Dir.left  => Pt(h.x - 1, h.y),
      Dir.right => Pt(h.x + 1, h.y),
    };

    if (nh.x < 0 || nh.x >= kGrid || nh.y < 0 || nh.y >= kGrid || _snake.contains(nh)) {
      _timer?.cancel();
      setState(() {
        _status = 'dead';
        if (_score > _highScore) _highScore = _score;
      });
      return;
    }

    final ns = [nh, ..._snake];
    if (nh == _food) {
      final fe = _foodEaten + 1;
      final lv = min((fe ~/ kFoodsPerLevel) + 1, kMaxLevel);
      final lvUp = lv > _level;
      setState(() { _snake = ns; _score += lv * 10; _foodEaten = fe; _level = lv; });
      _placeFood();
      if (lvUp) _resetTimer();
    } else {
      ns.removeLast();
      setState(() => _snake = ns);
    }
  }

  void _setDir(Dir d) {
    if (_status != 'running') return;
    if (d == Dir.up    && _dir == Dir.down)  return;
    if (d == Dir.down  && _dir == Dir.up)    return;
    if (d == Dir.left  && _dir == Dir.right) return;
    if (d == Dir.right && _dir == Dir.left)  return;
    _nextDir = d;
  }

  void _togglePause() {
    if (_status == 'running') {
      _timer?.cancel();
      setState(() => _status = 'paused');
    } else if (_status == 'paused') {
      setState(() => _status = 'running');
      _resetTimer();
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF1a1a2e),
      body: SafeArea(
        child: Column(
          children: [
            _hud(),
            Expanded(child: _canvas()),
            _controls(),
          ],
        ),
      ),
    );
  }

  Widget _hud() {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          _chip('نقاط: $_score'),
          _chip('مستوى: $_level'),
          _chip('أعلى: $_highScore'),
        ],
      ),
    );
  }

  Widget _chip(String t) => Container(
    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
    decoration: BoxDecoration(
      color: const Color(0xFF0f3460),
      borderRadius: BorderRadius.circular(8),
      border: Border.all(color: kAccent.withOpacity(0.3)),
    ),
    child: Text(t, style: const TextStyle(color: kAccent, fontSize: 12)),
  );

  Widget _canvas() {
    return Center(
      child: AspectRatio(
        aspectRatio: 1,
        child: Container(
          margin: const EdgeInsets.all(10),
          decoration: BoxDecoration(
            border: Border.all(color: kAccent, width: 2),
            borderRadius: BorderRadius.circular(8),
          ),
          child: GestureDetector(
            onVerticalDragEnd: (d) {
              if (d.velocity.pixelsPerSecond.dy.abs() > 100) {
                _setDir(d.velocity.pixelsPerSecond.dy < 0 ? Dir.up : Dir.down);
              }
            },
            onHorizontalDragEnd: (d) {
              if (d.velocity.pixelsPerSecond.dx.abs() > 100) {
                _setDir(d.velocity.pixelsPerSecond.dx < 0 ? Dir.left : Dir.right);
              }
            },
            child: ClipRRect(
              borderRadius: BorderRadius.circular(6),
              child: CustomPaint(
                painter: _Painter(snake: _snake, food: _food, dir: _dir),
                child: _status != 'running' ? _overlay() : null,
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _overlay() {
    final (title, msg) = switch (_status) {
      'idle'   => ('🐍 Snake Classic', 'اضغط ابدأ للعب'),
      'dead'   => ('💀 انتهت اللعبة!', 'النقاط: $_score | المستوى: $_level'),
      'paused' => ('⏸ متوقف', 'اضغط استئناف للمتابعة'),
      _        => ('', ''),
    };
    return Container(
      color: Colors.black.withOpacity(0.82),
      child: Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(title, style: const TextStyle(color: kAccent, fontSize: 22, fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            Text(msg, style: const TextStyle(color: Colors.white70, fontSize: 14)),
            const SizedBox(height: 18),
            if (_status != 'paused')
              ElevatedButton(
                onPressed: _start,
                style: ElevatedButton.styleFrom(
                  backgroundColor: kAccent,
                  foregroundColor: const Color(0xFF1a1a2e),
                ),
                child: const Text('▶ ابدأ اللعبة', style: TextStyle(fontWeight: FontWeight.bold)),
              ),
          ],
        ),
      ),
    );
  }

  Widget _controls() {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12, top: 4),
      child: Column(
        children: [
          SizedBox(
            width: 170,
            height: 170,
            child: GridView.count(
              crossAxisCount: 3,
              physics: const NeverScrollableScrollPhysics(),
              children: [
                const SizedBox(),
                _dpad('▲', () => _setDir(Dir.up)),
                const SizedBox(),
                _dpad('◀', () => _setDir(Dir.left)),
                Center(child: const Text('🐍', style: TextStyle(fontSize: 22))),
                _dpad('▶', () => _setDir(Dir.right)),
                const SizedBox(),
                _dpad('▼', () => _setDir(Dir.down)),
                const SizedBox(),
              ],
            ),
          ),
          const SizedBox(height: 8),
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              _btn(_status == 'paused' ? '▶ استئناف' : '⏸ إيقاف', _togglePause),
              const SizedBox(width: 10),
              _btn('↺ جديد', _start),
            ],
          ),
        ],
      ),
    );
  }

  Widget _dpad(String label, VoidCallback fn) => GestureDetector(
    onTapDown: (_) => fn(),
    child: Container(
      margin: const EdgeInsets.all(3),
      decoration: BoxDecoration(
        color: const Color(0xFF0f3460),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: kAccent.withOpacity(0.3)),
      ),
      child: Center(child: Text(label, style: const TextStyle(color: kAccent, fontSize: 22))),
    ),
  );

  Widget _btn(String label, VoidCallback fn) => GestureDetector(
    onTap: fn,
    child: Container(
      padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 9),
      decoration: BoxDecoration(
        color: const Color(0xFF0f3460),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: kAccent.withOpacity(0.3)),
      ),
      child: Text(label, style: const TextStyle(color: kAccent, fontSize: 13)),
    ),
  );
}

class _Painter extends CustomPainter {
  final List<Pt> snake;
  final Pt food;
  final Dir dir;

  const _Painter({required this.snake, required this.food, required this.dir});

  @override
  void paint(Canvas canvas, Size size) {
    final cell = size.width / kGrid;

    canvas.drawRect(Offset.zero & size, Paint()..color = kBgColor);

    final gp = Paint()..color = kGridColor..strokeWidth = 0.5;
    for (int i = 0; i <= kGrid; i++) {
      canvas.drawLine(Offset(i * cell, 0), Offset(i * cell, size.height), gp);
      canvas.drawLine(Offset(0, i * cell), Offset(size.width, i * cell), gp);
    }

    canvas.drawRRect(
      RRect.fromRectAndRadius(
        Rect.fromLTWH(food.x * cell + 2, food.y * cell + 2, cell - 4, cell - 4),
        const Radius.circular(3),
      ),
      Paint()..color = kFoodColor,
    );

    for (int i = 0; i < snake.length; i++) {
      final s = snake[i];
      final isHead = i == 0;
      final color = isHead ? kHeadColor : (i % 2 == 0 ? kBodyColor : kBodyDark);
      canvas.drawRRect(
        RRect.fromRectAndRadius(
          Rect.fromLTWH(s.x * cell + 1, s.y * cell + 1, cell - 2, cell - 2),
          Radius.circular(isHead ? 4 : 2),
        ),
        Paint()..color = color,
      );

      if (isHead && snake.length > 1) {
        final ep = Paint()..color = Colors.white;
        final hx = s.x * cell;
        final hy = s.y * cell;
        final (e1x, e1y, e2x, e2y) = switch (dir) {
          Dir.right => (hx + cell * .65, hy + cell * .2, hx + cell * .65, hy + cell * .6),
          Dir.left  => (hx + cell * .1,  hy + cell * .2, hx + cell * .1,  hy + cell * .6),
          Dir.up    => (hx + cell * .2,  hy + cell * .1, hx + cell * .6,  hy + cell * .1),
          Dir.down  => (hx + cell * .2,  hy + cell * .65, hx + cell * .6, hy + cell * .65),
        };
        final es = cell * 0.18;
        canvas.drawRect(Rect.fromLTWH(e1x, e1y, es, es), ep);
        canvas.drawRect(Rect.fromLTWH(e2x, e2y, es, es), ep);
      }
    }
  }

  @override
  bool shouldRepaint(_Painter o) => true;
}
