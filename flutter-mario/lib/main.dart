import 'dart:async';
import 'dart:math' as math;
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  SystemChrome.setPreferredOrientations([DeviceOrientation.portraitUp]);
  runApp(const App());
}

class App extends StatelessWidget {
  const App({super.key});
  @override
  Widget build(BuildContext context) => MaterialApp(
        debugShowCheckedModeBanner: false,
        home: const GameScreen(),
      );
}

// ================================================================
// Constants
// ================================================================
const double _G    = 0.45;     // gravity per tick
const double _JV   = -11.5;    // jump velocity
const double _SPD  = 3.8;      // horizontal speed
const double _VW   = 360.0;    // virtual viewport width
const double _VH   = 480.0;    // virtual viewport height
const double _GNY  = 420.0;    // ground top Y
const double _LW   = 2800.0;   // level total width

// ================================================================
// Models
// ================================================================
class Player {
  double x, y, vx = 0, vy = 0;
  bool onGround = false, facingRight = true;
  static const double W = 26.0, H = 32.0;
  Player(this.x, this.y);
  Rect get rect => Rect.fromLTWH(x, y, W, H);
}

class Plat {
  final double x, y, w, h;
  const Plat(this.x, this.y, this.w, this.h);
  Rect get rect => Rect.fromLTWH(x, y, w, h);
}

class Goomba {
  double x, y, vx, vy = 0;
  bool onGround = false, alive = true;
  static const double W = 26.0, H = 22.0;
  Goomba(this.x, this.y, this.vx);
  Rect get rect => Rect.fromLTWH(x, y, W, H);
}

class Coin {
  double x, y;
  bool taken = false;
  Coin(this.x, this.y);
  Rect get rect => Rect.fromLTWH(x - 9, y - 9, 18, 18);
}

// ================================================================
// Level Data
// ================================================================
List<Plat> _buildPlats() => const [
  Plat(0, _GNY, _LW, 80),           // Ground
  Plat(300, 340, 120, 20),
  Plat(520, 280, 100, 20),
  Plat(730, 340, 90, 20),
  Plat(920, 260, 130, 20),
  Plat(1140, 320, 100, 20),
  Plat(1350, 270, 110, 20),
  Plat(1560, 340, 90, 20),
  Plat(1760, 290, 120, 20),
  Plat(1970, 350, 100, 20),
  Plat(2180, 280, 140, 20),
  Plat(2400, 320, 100, 20),
  Plat(2600, 260, 120, 20),
];

List<Coin> _buildCoins() => [
  Coin(320, 300), Coin(360, 300), Coin(400, 300),
  Coin(545, 240), Coin(575, 240),
  Coin(945, 220), Coin(985, 220),
  Coin(1375, 230), Coin(1415, 230),
  Coin(1785, 250), Coin(1825, 250),
  Coin(2210, 240), Coin(2250, 240), Coin(2290, 240),
  Coin(2625, 220), Coin(2665, 220),
];

List<Goomba> _buildGoombas() => [
  Goomba(420,  _GNY - Goomba.H, -1.5),
  Goomba(610,  _GNY - Goomba.H,  1.2),
  Goomba(855,  _GNY - Goomba.H, -1.5),
  Goomba(555,  280  - Goomba.H,  1.0),
  Goomba(1200, _GNY - Goomba.H, -1.5),
  Goomba(1500, _GNY - Goomba.H,  1.2),
  Goomba(1380, 270  - Goomba.H, -1.0),
  Goomba(1810, _GNY - Goomba.H, -1.5),
  Goomba(2100, _GNY - Goomba.H,  1.5),
  Goomba(2460, _GNY - Goomba.H, -1.5),
];

// ================================================================
// Game State
// ================================================================
enum GState { start, playing, dead, win }

// ================================================================
// Main Widget
// ================================================================
class GameScreen extends StatefulWidget {
  const GameScreen({super.key});
  @override
  State<GameScreen> createState() => _GameScreenState();
}

class _GameScreenState extends State<GameScreen> {
  late Player _mario;
  late List<Plat> _plats;
  late List<Goomba> _goombas;
  late List<Coin> _coins;
  GState _gs = GState.start;
  int _score = 0, _lives = 3;
  double _cam = 0;
  Timer? _timer;
  bool _lDown = false, _rDown = false, _jumpQ = false;

  @override
  void initState() {
    super.initState();
    _resetLevel();
  }

  void _resetLevel() {
    _mario   = Player(60, _GNY - Player.H);
    _plats   = _buildPlats();
    _goombas = _buildGoombas();
    _coins   = _buildCoins();
    _cam     = 0;
  }

  void _startGame() {
    setState(() { _score = 0; _lives = 3; _resetLevel(); _gs = GState.playing; });
    _timer?.cancel();
    _timer = Timer.periodic(const Duration(milliseconds: 16), _tick);
  }

  void _respawn() {
    setState(() { _resetLevel(); _gs = GState.playing; });
    _timer?.cancel();
    _timer = Timer.periodic(const Duration(milliseconds: 16), _tick);
  }

  @override
  void dispose() { _timer?.cancel(); super.dispose(); }

  // ── Game Loop ──
  void _tick(Timer t) {
    setState(() {
      _updateMario();
      _updateGoombas();
      _checkCoins();
      _checkWin();
      _cam = (_mario.x + Player.W / 2 - _VW / 2).clamp(0.0, _LW - _VW);
    });
  }

  // ── Mario Physics ──
  void _updateMario() {
    final m = _mario;
    if (_lDown) { m.vx = -_SPD; m.facingRight = false; }
    else if (_rDown) { m.vx = _SPD; m.facingRight = true; }
    else m.vx = 0;

    if (_jumpQ && m.onGround) {
      m.vy = _JV;
      m.onGround = false;
      _jumpQ = false;
    } else if (!m.onGround) {
      _jumpQ = false;
    }

    m.vy = (m.vy + _G).clamp(-15.0, 14.0);

    // Move X → resolve
    m.x = (m.x + m.vx).clamp(0.0, _LW - Player.W);
    for (final p in _plats) _resolveX(m.rect, p, (ox) {
      m.x += (m.x + Player.W / 2 < p.x + p.w / 2) ? -ox : ox;
      m.vx = 0;
    });

    // Move Y → resolve
    m.y += m.vy;
    m.onGround = false;
    for (final p in _plats) _resolveY(m.rect, p, (oy, fromTop) {
      if (fromTop) { m.y -= oy; m.vy = 0; m.onGround = true; }
      else         { m.y += oy; m.vy = 0; }
    });

    if (m.y > _VH + 100) _die();
  }

  // ── Goomba Physics ──
  void _updateGoombas() {
    for (final g in _goombas) {
      if (!g.alive) continue;

      g.vy = (g.vy + _G).clamp(-15.0, 14.0);

      g.x += g.vx;
      if (g.x < 0) { g.x = 0; g.vx = g.vx.abs(); }
      if (g.x + Goomba.W > _LW) { g.x = _LW - Goomba.W; g.vx = -g.vx.abs(); }
      for (final p in _plats) _resolveX(g.rect, p, (ox) {
        g.x += (g.x + Goomba.W / 2 < p.x + p.w / 2) ? -ox : ox;
        g.vx = -g.vx;
      });

      g.y += g.vy;
      g.onGround = false;
      for (final p in _plats) _resolveY(g.rect, p, (oy, fromTop) {
        if (fromTop) { g.y -= oy; g.vy = 0; g.onGround = true; }
        else         { g.y += oy; g.vy = 0; }
      });

      // Mario/Goomba collision
      if (_mario.rect.overlaps(g.rect)) {
        final mr = _mario.rect;
        final gr = g.rect;
        if (_mario.vy > 0 && mr.bottom < gr.center.dy + 10) {
          g.alive = false;
          _mario.vy = _JV * 0.55;
          _score += 100;
        } else {
          _die();
        }
      }
    }
  }

  // ── Generic Collision Helpers ──
  double _ox(Rect a, Rect b) => math.min(a.right,  b.right)  - math.max(a.left, b.left);
  double _oy(Rect a, Rect b) => math.min(a.bottom, b.bottom) - math.max(a.top,  b.top);

  void _resolveX(Rect r, Plat p, void Function(double ox) apply) {
    if (!r.overlaps(p.rect)) return;
    final ox = _ox(r, p.rect);
    final oy = _oy(r, p.rect);
    if (ox <= 0 || oy <= 0 || ox >= oy) return;
    apply(ox);
  }

  void _resolveY(Rect r, Plat p, void Function(double oy, bool fromTop) apply) {
    if (!r.overlaps(p.rect)) return;
    final ox = _ox(r, p.rect);
    final oy = _oy(r, p.rect);
    if (ox <= 0 || oy <= 0 || oy >= ox) return;
    apply(oy, r.center.dy < p.rect.center.dy);
  }

  void _checkCoins() {
    for (final c in _coins) {
      if (!c.taken && _mario.rect.overlaps(c.rect)) {
        c.taken = true;
        _score += 50;
      }
    }
  }

  void _checkWin() {
    if (_mario.x >= _LW - 130) {
      _gs = GState.win;
      _timer?.cancel();
    }
  }

  void _die() {
    _lives--;
    if (_lives <= 0) { _gs = GState.dead; _timer?.cancel(); }
    else _resetLevel();
  }

  // ── Build ──
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      body: SafeArea(
        child: Column(children: [
          _hud(),
          Expanded(child: _gameArea()),
          _controls(),
        ]),
      ),
    );
  }

  Widget _hud() => Container(
    color: const Color(0xFF1E1E5E),
    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 7),
    child: Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
      Text('MARIO',          style: _hs),
      Text('SCORE: $_score', style: _hs),
      Text('LIVES: $_lives', style: _hs),
    ]),
  );

  static const _hs = TextStyle(
    color: Colors.white, fontWeight: FontWeight.bold,
    fontSize: 13, letterSpacing: 1,
  );

  Widget _gameArea() => LayoutBuilder(builder: (ctx, cons) {
    final scale = math.min(cons.maxWidth / _VW, cons.maxHeight / _VH);
    return GestureDetector(
      onTap: () {
        if (_gs == GState.start || _gs == GState.dead) _startGame();
        else if (_gs == GState.win) _startGame();
      },
      child: Center(
        child: SizedBox(
          width: _VW * scale,
          height: _VH * scale,
          child: CustomPaint(
            painter: _Painter(
              mario: _mario, plats: _plats, goombas: _goombas,
              coins: _coins, cam: _cam, gs: _gs, score: _score, scale: scale,
            ),
          ),
        ),
      ),
    );
  });

  Widget _controls() => Container(
    color: const Color(0xFF111111),
    padding: const EdgeInsets.symmetric(vertical: 10, horizontal: 20),
    child: Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
      Row(children: [
        _btn('◀',
          onDown: () => setState(() => _lDown = true),
          onUp:   () => setState(() => _lDown = false)),
        const SizedBox(width: 10),
        _btn('▶',
          onDown: () => setState(() => _rDown = true),
          onUp:   () => setState(() => _rDown = false)),
      ]),
      _btn('JUMP', wide: true,
        onDown: () => setState(() => _jumpQ = true),
        onUp:   () {}),
    ]),
  );

  Widget _btn(String label, {required VoidCallback onDown, required VoidCallback onUp, bool wide = false}) =>
    Listener(
      onPointerDown: (_) => onDown(),
      onPointerUp:   (_) => onUp(),
      onPointerCancel: (_) => onUp(),
      child: Container(
        width: wide ? 96 : 64, height: 64,
        decoration: BoxDecoration(
          color: const Color(0xFF2E2E6E),
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: Colors.white30, width: 2),
        ),
        alignment: Alignment.center,
        child: Text(label,
          style: const TextStyle(color: Colors.white, fontSize: 22, fontWeight: FontWeight.bold)),
      ),
    );
}

// ================================================================
// Painter
// ================================================================
class _Painter extends CustomPainter {
  final Player mario;
  final List<Plat> plats;
  final List<Goomba> goombas;
  final List<Coin> coins;
  final double cam, scale;
  final GState gs;
  final int score;

  const _Painter({
    required this.mario, required this.plats, required this.goombas,
    required this.coins, required this.cam, required this.gs,
    required this.score, required this.scale,
  });

  @override
  void paint(Canvas canvas, Size size) {
    canvas.save();
    canvas.scale(scale, scale);

    // Sky
    canvas.drawRect(const Rect.fromLTWH(0, 0, _VW, _VH),
        Paint()..color = const Color(0xFF5C94FC));

    _drawClouds(canvas);

    // World
    canvas.save();
    canvas.translate(-cam, 0);
    _drawPlats(canvas);
    _drawFlag(canvas);
    _drawCoins(canvas);
    _drawGoombas(canvas);
    _drawMario(canvas);
    canvas.restore();

    if (gs != GState.playing) _drawOverlay(canvas);

    canvas.restore();
  }

  // ── Clouds ──
  void _drawClouds(Canvas canvas) {
    final p = Paint()..color = Colors.white;
    _cloud(canvas, 40, 45, p);
    _cloud(canvas, 165, 32, p);
    _cloud(canvas, 285, 52, p);
  }

  void _cloud(Canvas canvas, double x, double y, Paint p) {
    canvas.drawCircle(Offset(x,      y),      18, p);
    canvas.drawCircle(Offset(x + 22, y - 9),  24, p);
    canvas.drawCircle(Offset(x + 46, y),      17, p);
  }

  // ── Platforms ──
  void _drawPlats(Canvas canvas) {
    final dirt  = Paint()..color = const Color(0xFF8B5E3C);
    final grass = Paint()..color = const Color(0xFF4CAF50);
    final brick = Paint()..color = const Color(0xFFCD7F32);
    final bLine = Paint()..color = const Color(0xFF8B4513)..strokeWidth = 1.0
        ..style = PaintingStyle.stroke;

    for (final p in plats) {
      if (p.h > 30) {
        canvas.drawRect(Rect.fromLTWH(p.x, p.y, p.w, 14), grass);
        canvas.drawRect(Rect.fromLTWH(p.x, p.y + 14, p.w, p.h - 14), dirt);
        for (double gx = p.x + 8; gx < p.x + p.w - 4; gx += 22) {
          canvas.drawCircle(Offset(gx, p.y + 5), 5, grass);
        }
      } else {
        canvas.drawRRect(RRect.fromRectAndRadius(p.rect, const Radius.circular(3)), brick);
        for (double bx = p.x + 16; bx < p.x + p.w; bx += 16) {
          canvas.drawLine(Offset(bx, p.y), Offset(bx, p.y + p.h), bLine);
        }
        canvas.drawLine(
          Offset(p.x, p.y + p.h * 0.5),
          Offset(p.x + p.w, p.y + p.h * 0.5), bLine);
      }
    }
  }

  // ── Goal Flag ──
  void _drawFlag(Canvas canvas) {
    const fx = _LW - 110.0;
    final pole = Paint()..color = const Color(0xFFBBBBBB);
    final flag = Paint()..color = const Color(0xFF22DD44);
    final base = Paint()..color = const Color(0xFF888888);

    canvas.drawRect(Rect.fromLTWH(fx + 18, _GNY - 165, 7, 165), pole);
    canvas.drawPath(
      Path()
        ..moveTo(fx + 25, _GNY - 165)
        ..lineTo(fx + 72, _GNY - 145)
        ..lineTo(fx + 25, _GNY - 125),
      flag,
    );
    canvas.drawRRect(
      RRect.fromRectAndRadius(Rect.fromLTWH(fx + 8, _GNY - 14, 36, 14), const Radius.circular(3)),
      base,
    );
  }

  // ── Coins ──
  void _drawCoins(Canvas canvas) {
    final gold  = Paint()..color = const Color(0xFFFFD700);
    final shine = Paint()..color = const Color(0xFFFFF8AA);
    for (final c in coins) {
      if (c.taken) continue;
      canvas.drawCircle(Offset(c.x, c.y), 9, gold);
      canvas.drawCircle(Offset(c.x - 2, c.y - 2), 3, shine);
    }
  }

  // ── Goombas ──
  void _drawGoombas(Canvas canvas) {
    final body  = Paint()..color = const Color(0xFF7A3B00);
    final feet  = Paint()..color = const Color(0xFF3D1C00);
    final white = Paint()..color = Colors.white;
    final black = Paint()..color = Colors.black;
    final brow  = Paint()..color = const Color(0xFF1A0A00)
        ..strokeWidth = 2.5..style = PaintingStyle.stroke;

    for (final g in goombas) {
      if (!g.alive) continue;
      final x = g.x, y = g.y;
      canvas.drawRRect(
        RRect.fromRectAndRadius(Rect.fromLTWH(x, y + 6, Goomba.W, Goomba.H - 6), const Radius.circular(5)),
        body,
      );
      canvas.drawOval(Rect.fromLTWH(x - 2, y, Goomba.W + 4, 16), body);
      // Angry brows
      canvas.drawLine(Offset(x + 3, y + 3),  Offset(x + 10, y + 7), brow);
      canvas.drawLine(Offset(x + 23, y + 3), Offset(x + 16, y + 7), brow);
      // Eyes
      canvas.drawOval(Rect.fromLTWH(x + 3,  y + 5, 8, 7), white);
      canvas.drawOval(Rect.fromLTWH(x + 15, y + 5, 8, 7), white);
      canvas.drawCircle(Offset(x + 7,  y + 8), 2.5, black);
      canvas.drawCircle(Offset(x + 19, y + 8), 2.5, black);
      // Feet
      canvas.drawOval(Rect.fromLTWH(x,      y + Goomba.H - 5, 13, 5), feet);
      canvas.drawOval(Rect.fromLTWH(x + 13, y + Goomba.H - 5, 13, 5), feet);
    }
  }

  // ── Mario ──
  void _drawMario(Canvas canvas) {
    final x = mario.x, y = mario.y;
    canvas.save();
    if (!mario.facingRight) {
      canvas.translate(x + Player.W, 0);
      canvas.scale(-1, 1);
      canvas.translate(-x, 0);
    }

    final red    = Paint()..color = const Color(0xFFE52222);
    final skin   = Paint()..color = const Color(0xFFFFCC99);
    final blue   = Paint()..color = const Color(0xFF2244CC);
    final brown  = Paint()..color = const Color(0xFF7A3B00);
    final black  = Paint()..color = Colors.black;
    final dRed   = Paint()..color = const Color(0xFF8B0000);

    // Shoes
    canvas.drawRRect(RRect.fromRectAndRadius(Rect.fromLTWH(x + 1,  y + 26, 11, 6), const Radius.circular(2)), brown);
    canvas.drawRRect(RRect.fromRectAndRadius(Rect.fromLTWH(x + 14, y + 26, 11, 6), const Radius.circular(2)), brown);
    // Overalls
    canvas.drawRect(Rect.fromLTWH(x + 4, y + 16, 18, 12), blue);
    canvas.drawRect(Rect.fromLTWH(x + 4, y + 13,  8,  4), blue);
    canvas.drawRect(Rect.fromLTWH(x + 14, y + 13, 8,  4), blue);
    // Arms
    canvas.drawRect(Rect.fromLTWH(x,      y + 16, 5, 10), red);
    canvas.drawRect(Rect.fromLTWH(x + 21, y + 16, 5, 10), red);
    canvas.drawCircle(Offset(x + 2,  y + 26), 3, skin);
    canvas.drawCircle(Offset(x + 24, y + 26), 3, skin);
    // Face
    canvas.drawRect(Rect.fromLTWH(x + 5, y + 8, 16, 11), skin);
    // Eye
    canvas.drawRect(Rect.fromLTWH(x + 14, y + 10, 4, 4), black);
    // Nose
    canvas.drawOval(Rect.fromLTWH(x + 11, y + 13, 9, 4), skin);
    // Mustache
    canvas.drawOval(Rect.fromLTWH(x + 7,  y + 15, 8, 3), brown);
    canvas.drawOval(Rect.fromLTWH(x + 14, y + 15, 8, 3), brown);
    // Hat brim
    canvas.drawRect(Rect.fromLTWH(x,     y + 7, 26, 4), red);
    // Hat top
    canvas.drawRect(Rect.fromLTWH(x + 3, y + 1, 20, 8), red);
    // Hat band
    canvas.drawRect(Rect.fromLTWH(x + 3, y + 7, 20, 2), dRed);

    canvas.restore();
  }

  // ── Overlay ──
  void _drawOverlay(Canvas canvas) {
    canvas.drawRect(
      const Rect.fromLTWH(0, 0, _VW, _VH),
      Paint()..color = const Color(0xCC000000),
    );

    late String title, subtitle;
    switch (gs) {
      case GState.start:
        title    = 'SUPER MARIO';
        subtitle = 'اضغط على الشاشة للبدء';
      case GState.dead:
        title    = 'GAME OVER';
        subtitle = 'اضغط لإعادة اللعب';
      case GState.win:
        title    = 'YOU WIN!';
        subtitle = 'النقاط: $score\nاضغط لإعادة اللعب';
      default:
        return;
    }

    void pt(String text, double top, double sz, Color color, {bool bold = false}) {
      final tp = TextPainter(
        text: TextSpan(text: text,
            style: TextStyle(color: color, fontSize: sz,
                fontWeight: bold ? FontWeight.bold : FontWeight.normal)),
        textDirection: TextDirection.ltr,
        textAlign: TextAlign.center,
      )..layout(maxWidth: _VW);
      tp.paint(canvas, Offset((_VW - tp.width) / 2, top));
    }

    pt(title, 155, 34, const Color(0xFFFFD700), bold: true);
    pt(subtitle, 210, 18, Colors.white);
    if (gs == GState.start) {
      pt('Collect coins  |  Stomp enemies  |  Reach the flag', 260, 11, Colors.white60);
    }
  }

  @override
  bool shouldRepaint(covariant CustomPainter old) => true;
}
