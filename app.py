<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8" />
    <script src="https://cdnjs.cloudflare.com/ajax/libs/p5.js/1.9.4/p5.min.js"></script>
  </head>
  <body>
    <script>
      // Dream/Memory Doodler — Birthday with childhood friends
      // Palette: coral → gold → lavender
      let centerPos, orbitR, nodes = [], caption = "October 25 — Old friends, new laughter";

      function setup() {
        createCanvas(900, 900);
        centerPos = createVector(width/2, height/2);
        orbitR = min(width, height) * 0.28;

        // set up 10 nodes around a ring
        const N = 10;
        for (let i = 0; i < N; i++) {
          const a = TWO_PI * i / N - PI/2;
          nodes.push({
            base: createVector(centerPos.x + orbitR * cos(a), centerPos.y + orbitR * sin(a)),
            phase: random(TWO_PI)
          });
        }
        textFont('Georgia');
      }

      function draw() {
        drawBackgroundGradient();
        noFill();

        // gentle outer ripples (laughter echoes)
        push();
        translate(centerPos.x, centerPos.y);
        const t = frameCount * 0.01;
        for (let i = 0; i < 6; i++) {
          const r = map((t + i * 0.35) % 1, 0, 1, orbitR * 0.9, orbitR * 1.6);
          stroke(255, 215, 130, map(r, orbitR*0.9, orbitR*1.6, 90, 0));  // golden, fading
          strokeWeight(1.25);
          circle(0, 0, r * 2);
        }
        pop();

        // threads between nodes (connections)
        stroke(230, 180, 90, 120);
        strokeWeight(1.3);
        for (let i = 0; i < nodes.length; i++) {
          const a = nodes[i].base;
          // center → node
          line(centerPos.x, centerPos.y, a.x, a.y);
          // node → next node (ring)
          const b = nodes[(i+1) % nodes.length].base;
          bezier(a.x, a.y,
                 lerp(a.x, centerPos.x, 0.25), lerp(a.y, centerPos.y, 0.25),
                 lerp(b.x, centerPos.x, 0.25), lerp(b.y, centerPos.y, 0.25),
                 b.x, b.y);
        }

        // central glow (the birthday moment)
        drawGlow(centerPos.x, centerPos.y, min(width, height)*0.16, color(255, 195, 80, 130));
        fill(255, 190, 70, 200);
        noStroke();
        circle(centerPos.x, centerPos.y, min(width, height)*0.11);

        // orbiting friend nodes (slight breathing)
        for (let i = 0; i < nodes.length; i++) {
          const n = nodes[i];
          const breathe = 4 * sin(frameCount*0.02 + n.phase);
          const x = n.base.x + breathe * (n.base.x - centerPos.x) / orbitR * 2;
          const y = n.base.y + breathe * (n.base.y - centerPos.y) / orbitR * 2;

          // subtle echo circle (memory drift)
          noFill();
          stroke(130, 90, 60, 70);
          strokeWeight(2);
          circle(x+2, y+2, 56);

          // node
          fill(255, 205, 120, 170);
          stroke(140, 90, 60, 120);
          strokeWeight(1.8);
          circle(x, y, 46);
        }

        // caption
        noStroke();
        fill(70, 60, 65, 200);
        textSize(28);
        textAlign(RIGHT, BOTTOM);
        text(caption, width - 36, height - 32);
      }

      // --- Helpers ---
      function drawBackgroundGradient() {
        // linear gradient top-left (coral) → center (gold) → top-right (lavender)
        const coral = color(247, 152, 146);
        const gold  = color(255, 212, 130);
        const lav   = color(192, 165, 215);

        // vertical blend coral → gold
        for (let y = 0; y < height; y++) {
          const f = y / height;
          const c = lerpColor(coral, gold, f);
          stroke(c);
          line(0, y, width, y);
        }
        // overlay radial lavender tint from upper-right corner
        noStroke();
        for (let r = 0; r < 600; r++) {
          const a = map(r, 0, 600, 110, 0);
          fill(red(lav), green(lav), blue(lav), a*0.3);
          circle(width*0.85, height*0.15, r);
        }
        // add paper texture noise
        loadPixels();
        for (let i = 0; i < pixels.length; i += 4) {
          const n = random(-8, 8);
          pixels[i]   = constrain(pixels[i]   + n, 0, 255);
          pixels[i+1] = constrain(pixels[i+1] + n, 0, 255);
          pixels[i+2] = constrain(pixels[i+2] + n, 0, 255);
        }
        updatePixels();
      }

      function drawGlow(x, y, radius, col) {
        noStroke();
        for (let r = radius; r > 0; r -= 6) {
          const a = map(r, 0, radius, 220, 0);
          fill(red(col), green(col), blue(col), a*0.5);
          circle(x, y, r*2);
        }
      }

      // Press 's' to save a PNG snapshot
      function keyPressed() {
        if (key === 's' || key === 'S') {
          saveCanvas('memory_birthday_friends', 'png');
        }
      }
    </script>
  </body>
</html>
