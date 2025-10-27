p5_html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset='utf-8'>
<meta name='x-schema-hash' content='{schema_hash}'>
<style>
html,body {{margin:0;padding:0;background:#faf7f5;}}
#wrap {{position:relative;width:900px;margin:0 auto;}}
#btnsave {{
  position:absolute;top:12px;right:12px;z-index:10;
  padding:8px 12px;border:1px solid #d9cbb9;border-radius:8px;background:#fff;
  font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;cursor:pointer;
}}
#caption {{
  position:absolute;bottom:10px;right:16px;color:rgba(70,60,65,0.85);font-size:18px;
  font-family:Georgia,serif;pointer-events:none;text-shadow:0 1px 0 rgba(255,255,255,0.4);
}}
canvas {{border-radius:12px;box-shadow:0 10px 30px rgba(0,0,0,0.06);}}
</style>
</head>
<body>
<div id='wrap' data-schema-hash='{schema_hash}'>
  <button id='btnsave' onclick='savePNG()'>Download PNG</button>
  <div id='p5mount'></div>
  <div id='caption'></div>
</div>

<script src='https://cdnjs.cloudflare.com/ajax/libs/p5.js/1.9.4/p5.min.js'></script>
<script>
const SCHEMA = {schema_js};

function hashString(s){{ let h=2166136261>>>0; for(let i=0;i<s.length;i++){{ h^=s.charCodeAt(i); h=Math.imul(h,16777619); }} return h>>>0; }}
const SEED=hashString((SCHEMA.caption||'')+'|'+(SCHEMA.emotion||'')+'|'+(SCHEMA.nodes||'')+'|'+JSON.stringify(SCHEMA.palette||[]));
const LAYOUT=(SEED%3),RIPPLE_COUNT=4+(SEED%5),THREAD_OPACITY=80+(SEED%60),BG_ANGLE=(SEED%360)*Math.PI/180,BREATH_BASE=0.015+(SCHEMA.intensity?SCHEMA.intensity*0.025:0.02);

let centerPos,orbitR,nodes=[];
new p5((p)=>{{
  p.setup=function(){{
    p.randomSeed(SEED); p.noiseSeed(SEED);
    const c=p.createCanvas(900,900); c.parent(document.getElementById('p5mount'));
    centerPos=p.createVector(p.width/2,p.height/2);
    orbitR=Math.min(p.width,p.height)*(0.22+(SEED%8)*0.01);
    const N=Math.max(3,Math.min(20,SCHEMA.nodes||10));

    if(LAYOUT===0) {{
      for(let i=0;i<N;i++) {{
        const a=p.TWO_PI*i/N-p.PI/2;
        const rJit=orbitR*(0.9+p.random()*0.2);
        nodes.push({{x:centerPos.x+rJit*Math.cos(a),y:centerPos.y+rJit*Math.sin(a),phase:p.random(p.TWO_PI)}});
      }}
    }} else if(LAYOUT===1) {{
      const step=orbitR*(1.0/N);
      for(let i=0;i<N;i++) {{
        const a=(i*0.9)+(SEED%10)*0.03; const r=step*(i+3);
        nodes.push({{x:centerPos.x+r*Math.cos(a),y:centerPos.y+r*Math.sin(a),phase:p.random(p.TWO_PI)}});
      }}
    }} else {{
      const clusters=2+(SEED%2);
      const centers=[];
      for(let k=0;k<clusters;k++) {{
        const ang=(k/clusters)*p.TWO_PI+0.6*(SEED%7);
        const rad=orbitR*0.6;
        centers.push({{x:centerPos.x+rad*Math.cos(ang),y:centerPos.y+rad*Math.sin(ang)}});
      }}
      for(let i=0;i<N;i++) {{
        const cidx=i%clusters; const cx=centers[cidx].x, cy=centers[cidx].y;
        const r=50+p.random(80), a=p.random(p.TWO_PI);
        nodes.push({{x:cx+r*Math.cos(a),y:cy+r*Math.sin(a),phase:p.random(p.TWO_PI)}});
      }}
    }}

    document.getElementById('caption').textContent=SCHEMA.caption||'';
  }};

  p.draw=function(){{
    drawBackground(p,SCHEMA.palette||['#F79892','#FFD482','#C0A5D7']);
    p.noFill();

    // ripples
    p.push(); p.translate(centerPos.x,centerPos.y);
    const t=p.frameCount*0.01;
    for(let i=0;i<RIPPLE_COUNT;i++) {{
      const baseIn=orbitR*0.85, baseOut=orbitR*1.65;
      const r=p.map((t+i*0.25)%1,0,1,baseIn,baseOut);
      p.stroke(255,215,130,p.map(r,baseIn,baseOut,90,0));
      p.strokeWeight(1.25); p.circle(0,0,r*2);
    }}
    p.pop();

    // threads
    p.stroke(230,180,90,THREAD_OPACITY); p.strokeWeight(1.3);
    for(let i=0;i<nodes.length;i++) {{
      const a=nodes[i]; const b=nodes[(i+1)%nodes.length];
      p.line(centerPos.x,centerPos.y,a.x,a.y);
      p.bezier(a.x,a.y,
               p.lerp(a.x,centerPos.x,0.25), p.lerp(a.y,centerPos.y,0.25),
               p.lerp(b.x,centerPos.x,0.25), p.lerp(b.y,centerPos.y,0.25),
               b.x,b.y);
    }}

    // center glow
    drawGlow(p,centerPos.x,centerPos.y,Math.min(p.width,p.height)*0.16,p.color(255,195,80,130));
    p.fill(255,190,70,200); p.noStroke();
    p.circle(centerPos.x,centerPos.y,Math.min(p.width,p.height)*0.11);

    // nodes
    for(let i=0;i<nodes.length;i++) {{
      const n=nodes[i]; const breathe=4*Math.sin(p.frameCount*BREATH_BASE+n.phase);
      const vx=n.x+breathe*0.8, vy=n.y+breathe*0.8;
      p.noFill(); p.stroke(130,90,60,70); p.strokeWeight(2); p.circle(vx+2,vy+2,54);
      p.fill(255,205,120,170); p.stroke(140,90,60,120); p.strokeWeight(1.8); p.circle(vx,vy,44);
    }}
  }};
}});

function drawBackground(p,palette){{
  const c1=p.color(palette[0]), c2=p.color(palette[1]), c3=p.color(palette[2]);
  for(let y=0;y<p.height;y++){{ const f=y/(p.height-1); const col=p.lerpColor(c1,c2,f); p.stroke(col); p.line(0,y,p.width,y); }}
  p.noStroke(); for(let r=0;r<600;r++){{ const a=p.map(r,0,600,110,0); p.fill(p.red(c3),p.green(c3),p.blue(c3),a*0.3); p.circle(p.width*0.85,p.height*0.15,r); }}
}}

function drawGlow(p,x,y,radius,col){{
  p.noStroke(); for(let r=radius;r>0;r-=6){{ const a=p.map(r,0,radius,220,0); p.fill(p.red(col),p.green(col),p.blue(col),a*0.5); p.circle(x,y,r*2); }}
}}

function savePNG(){{
  const c=document.querySelector('canvas'); if(!c) return;
  const link=document.createElement('a'); link.download='memory_doodle.png'; link.href=c.toDataURL('image/png'); link.click();
}}
</script>
</body>
</html>
"""
