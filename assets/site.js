
// 站点根路径（本脚本位于 assets/ 下，因此上一级即根）
const SITE_ROOT=new URL('..',document.currentScript.src).href;

// 移动端导航汉堡
const navToggle=document.querySelector('.navtoggle');
const topNav=document.querySelector('.topnav');
if(navToggle&&topNav){
  navToggle.addEventListener('click',()=>{
    const open=topNav.classList.toggle('open');
    navToggle.setAttribute('aria-expanded',open?'true':'false');
    navToggle.textContent=open?'关闭':'菜单';
  });
}

// 导航下拉：键盘与触屏可达（悬停之外再给一条路）
document.querySelectorAll('.navitem').forEach(item=>{
  const label=item.querySelector('.navlabel');if(!label)return;
  label.setAttribute('tabindex','0');label.setAttribute('role','button');
  label.setAttribute('aria-haspopup','true');label.setAttribute('aria-expanded','false');
  const set=v=>{item.classList.toggle('open',v);label.setAttribute('aria-expanded',v?'true':'false');};
  label.addEventListener('click',()=>set(!item.classList.contains('open')));
  label.addEventListener('keydown',e=>{
    if(e.key==='Enter'||e.key===' '){e.preventDefault();set(!item.classList.contains('open'));}
    else if(e.key==='Escape')set(false);
  });
  item.addEventListener('focusout',e=>{if(!item.contains(e.relatedTarget))set(false);});
});

// 当前页高亮（下拉项 + 顶栏直链）
(function(){
  const here=location.pathname.replace(/index\.html$/,'');
  document.querySelectorAll('.topnav a').forEach(a=>{
    if(a.hash)return;
    const ap=new URL(a.href).pathname.replace(/index\.html$/,'');
    if(ap===here){
      a.classList.add('current');a.setAttribute('aria-current','page');
      const item=a.closest('.navitem');
      if(item)item.querySelector('.navlabel').classList.add('current');
    }
  });
})();

// 阅读进度条
const bar=document.getElementById('progress');
if(bar){addEventListener('scroll',()=>{const h=document.documentElement;
  bar.style.width=(h.scrollTop/(h.scrollHeight-h.clientHeight)*100)+'%';},{passive:true});}

// 目录高亮（章节页）
const navLinks=[...document.querySelectorAll('.trailnav a[href^="#"]')];
if(navLinks.length){
  const map=new Map(navLinks.map(a=>[a.getAttribute('href').slice(1),a]));
  const obs=new IntersectionObserver(es=>{es.forEach(e=>{const a=map.get(e.target.id);
    if(a&&e.isIntersecting){navLinks.forEach(x=>x.classList.remove('on'));a.classList.add('on');}});},
    {rootMargin:'-20% 0px -70% 0px'});
  map.forEach((a,id)=>{const el=document.getElementById(id);if(el)obs.observe(el);});
}

// 通用交互图挂载：nodes 带 data-k，面板按 data-set 取数据
const DATASETS={

// 首页：L0/L1/L2 结构（公众化转述，非 canonical 定义源；见 MANIFEST）
levels:{
 l0:{t:'L0 · 潜在域',c:'#868A7B',loc:'尚未被确定的可能',
   b:'不是虚无，而是尚未被确定的可能性：还没有被压成某一种现实，但并非什么都没有。'},
 sel:{t:'选择 · 约束 · 代价',c:'#A97036',loc:'从可能到显现',
   b:'把某种可能性压入现实，并让其他可能性退出、延迟、沉默。它不是轻飘飘的主观偏好——身体、历史、环境、制度、代价和后果都在约束它。'},
 l1:{t:'L1 · 显现域',c:'#575C4F',loc:'此时此地',
   b:'某种可能性在具体位置被选出，进入“此时此地可以被遭遇、处理、承担”的状态。私人感受若穿不过约束、阻力和后果的测试，还不是稳定意义上的显现。'},
 sed:{t:'重复 · 记录 · 继承',c:'#A97036',loc:'从显现到收敛',
   b:'某些显现被反复选择、维持、记录、继承——痕迹沉积出厚度，结构开始承重。'},
 l2:{t:'L2 · 收敛域',c:'#7C5023',loc:'共同世界',
   b:'稳定结构：习惯、身份、语言、市场、制度、科学对象、共同世界。越稳定，越容易被误认为“本来就如此”——稳定说明它撑住了，不等于它天然、正当、无需追问。'},
 psi:{t:'Ψf · 本体论摩擦',c:'#255449',loc:'现实为什么变硬',
   b:'一个现实结构要持续存在，必须有人、某个系统或某种机制替它支付维持成本。现实之所以变硬，不是因为不可改变，而是因为重新选择要付出代价。'},
 dv:{t:'d-value · 关切深度',c:'#255449',loc:'价值不是偏好',
   b:'不是普通偏好或奖励函数，而是一个问题：这件事是否关系到一个系统还能成为什么？价值开始于后果无法被完全外包、替换或抹平的地方。'}
},

// 书稿页：图0 主梁总图
beam:{
 k1:{t:'尚未成形的可能',c:'var(--ink-faint)',loc:'序章 · 第一幕',
   b:'还没有成形的不是虚无，而是尚未被压成某一种现实的可能。全书从这里出发：先拆掉“世界本来就是现成对象摆在那里”的默认地板。'},
 k2:{t:'选择排开其他可能',c:'var(--ink-soft)',loc:'第五、六章',
   b:'不是所有可能都能同时留下。有了“这个”，就必须有“不是这个”——而被排开的并没有变成纯粹的无。'},
 k3:{t:'显现成一个结果',c:'var(--ink-soft)',loc:'第二幕',
   b:'某个方向获得边界，成为可辨识、可遭遇的“一个”。它不是从菜单里挑出来的，而是当场显影。'},
 k4:{t:'结果留下痕迹',c:'var(--stay)',loc:'第七、八章',
   b:'结果写入后续条件——这是最小的痕迹。痕迹如何经由留痕、承重、再入场，硬化成撤不回去的历史重量，是“锚定”要讲的事。'},
 k5:{t:'痕迹沉积为地形',c:'var(--stay-deep)',loc:'第九、十章',
   b:'多次写入叠出厚度，地形隐去、退成背景，开始显得“本来如此”。稳定不是起点，而是选择留下来的历史。'},
 k6:{t:'地形安排下一次选择',c:'var(--ink-soft)',loc:'第十、十一章',
   b:'地形预先塑形下一轮菜单。你以为是起点的东西，其实是结果。'},
 k7:{t:'后果能否回到承受位置？',c:'var(--ink)',loc:'第三、四幕',
   b:'全书主判据。这不是道德口号，而是区分“活稳定”与“死稳定”的结构问题：稳定之后，后果还穿得过这个结构吗？'},
 k8:{t:'能回来：生成继续',c:'var(--ret-deep)',loc:'第十二、十三章起',
   b:'后果回到一个在乎它的位置：学习、修复、价值、主体生长——秩序托举下一次生成。'},
 k9:{t:'回不来：稳定，但生成停止',c:'var(--lock-deep)',loc:'第十九、二十、二十三章',
   b:'外包：别人承受，我继续选择。遮蔽：指标回来了，真实后果没回来。锁死：系统还稳定，但生成已经停止。'}
}
};

document.querySelectorAll('.idetail[data-set]').forEach(panel=>{
  const data=DATASETS[panel.dataset.set];if(!data)return;
  const fig=document.getElementById(panel.dataset.fig);if(!fig)return;
  const nodes=[...fig.querySelectorAll('.bnode')];
  const show=k=>{const d=data[k];if(!d)return;
    nodes.forEach(n=>n.classList.toggle('active',n.dataset.k===k));
    panel.innerHTML='<div class="bd-title"><span class="bd-dot" style="background:'+d.c+'"></span>'+d.t+
      '</div><p>'+d.b+'</p><div class="bd-loc">'+d.loc+'</div>';};
  nodes.forEach(n=>{n.addEventListener('click',()=>show(n.dataset.k));
    n.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();show(n.dataset.k);}});});
  show(panel.dataset.default||nodes[0].dataset.k);
});

// ================= 顺读动线：上一页 / 下一页 =================
(function(){
  const ORDER=[
    ['index.html','首页 · 现实不是先给定的'],
    ['corelaw.html','核心律法 · 七条论纲'],
    ['l0.html','L0 形而上学 · 地基'],
    ['theory.html','理论核心 · P0 / P1'],
    ['equations.html','方程层 · 四条主方程'],
    ['operator.html','选择算子 Ĝθ'],
    ['dynamics.html','动力学与尺度'],
    ['l2.html','L₂ 本体论 · 活/死稳定'],
    ['individuation.html','个体化 · 主体的凝结'],
    ['collective.html','集体选择 · 后果回流'],
    ['predictions.html','判别性预测 · 可证伪'],
    ['domains.html','跨域显影 · 五域'],
    ['domains/phys.html','显影 · 物理'],
    ['domains/bio.html','显影 · 生物'],
    ['domains/soc.html','显影 · 社会'],
    ['domains/ai.html','显影 · 人工智能'],
    ['domains/mind.html','显影 · 主体意识'],
    ['consciousness.html','意识 · 困难问题消解'],
    ['ai.html','AI · 赌注与主体门槛'],
    ['philosophy.html','哲学延伸 · 大问题'],
    ['spirituality.html','灵性与宗教语言'],
    ['comparison.html','理论对照 · vs 七框架'],
    ['methodology.html','方法与治理'],
    ['book/index.html','书稿《从存在到秩序》'],
    ['book/q05.html','公开样章 · 第五章'],
    ['articles.html','文章 ·《活的选择》'],
    ['value-hiddenness.html','价值不是缺席的，是被遮蔽的'],
    ['video.html','视频 · 三层结构'],
    ['papers.html','论文集'],
    ['map.html','全站理论地图']
  ];
  const rootPath=new URL(SITE_ROOT).pathname;
  let rel=location.pathname.startsWith(rootPath)?location.pathname.slice(rootPath.length):null;
  if(rel==='')rel='index.html';
  const i=ORDER.findIndex(o=>o[0]===rel);
  if(i<1)return; // 首页与站外页不挂 pager
  const guard=document.querySelector('.guardrails');if(!guard)return;
  const prev=ORDER[i-1],next=ORDER[i+1];
  const el=document.createElement('nav');
  el.className='pager';el.setAttribute('aria-label','顺读导航');
  el.innerHTML='<div class="wrap">'
    +(prev?'<a class="pg prev" href="'+SITE_ROOT+prev[0]+'"><span>← 上一页</span><b>'+prev[1]+'</b></a>':'<span class="pg"></span>')
    +'<a class="pg mid" href="'+SITE_ROOT+'map.html">全站地图</a>'
    +(next?'<a class="pg next" href="'+SITE_ROOT+next[0]+'"><span>下一页 →</span><b>'+next[1]+'</b></a>':'<span class="pg"></span>')
    +'</div>';
  guard.parentNode.insertBefore(el,guard);
})();

// 回到顶部
(function(){
  const b=document.createElement('button');
  b.className='totop';b.type='button';b.setAttribute('aria-label','回到顶部');
  b.innerHTML='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" width="17" height="17"><path d="M12 19V6M5 12l7-7 7 7"/></svg>';
  document.body.appendChild(b);
  b.addEventListener('click',()=>scrollTo({top:0,behavior:'smooth'}));
  addEventListener('scroll',()=>{b.classList.toggle('show',scrollY>600);},{passive:true});
})();

// ================= 全站搜索（⌘K / Ctrl+K） =================
(function(){
  const bar=document.querySelector('.topbar .wrap');
  if(!bar)return;
  const btn=document.createElement('button');
  btn.className='searchbtn';btn.type='button';
  btn.setAttribute('aria-label','搜索全站');
  btn.innerHTML='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><circle cx="11" cy="11" r="7"/><path d="M21 21l-4.5-4.5"/></svg><span>搜索</span><kbd>'+(navigator.platform.indexOf('Mac')>-1?'⌘K':'Ctrl K')+'</kbd>';
  const toggleBtn=bar.querySelector('.navtoggle');
  bar.insertBefore(btn,toggleBtn?toggleBtn.nextSibling:null);

  let overlay=null,input=null,resBox=null,idx=null,sel=0,results=[];
  const esc=s=>s.replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
  const rxesc=s=>s.replace(/[.*+?^${}()|[\]\\]/g,'\\$&');

  function build(){
    overlay=document.createElement('div');
    overlay.className='search-overlay';overlay.hidden=true;
    overlay.innerHTML='<div class="search-panel" role="dialog" aria-modal="true" aria-label="全站搜索">'
      +'<div class="search-input-row"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" width="17" height="17"><circle cx="11" cy="11" r="7"/><path d="M21 21l-4.5-4.5"/></svg>'
      +'<input class="search-input" type="search" placeholder="搜索概念、章节、判据…" aria-label="搜索关键词" autocomplete="off"/></div>'
      +'<div class="search-res" role="listbox"></div>'
      +'<div class="search-foot"><span>↑↓ 选择</span><span>Enter 打开</span><span>Esc 关闭</span></div></div>';
    document.body.appendChild(overlay);
    input=overlay.querySelector('.search-input');
    resBox=overlay.querySelector('.search-res');
    overlay.addEventListener('mousedown',e=>{if(e.target===overlay)close();});
    input.addEventListener('input',()=>render(input.value));
    input.addEventListener('keydown',e=>{
      if(e.key==='ArrowDown'){e.preventDefault();move(1);}
      else if(e.key==='ArrowUp'){e.preventDefault();move(-1);}
      else if(e.key==='Enter'){const a=resBox.querySelector('a.sel');if(a)location.href=a.href;}
    });
  }
  function open(){
    if(!overlay)build();
    overlay.hidden=false;document.documentElement.style.overflow='hidden';
    input.value='';render('');input.focus();
    if(!idx)fetch(SITE_ROOT+'assets/search-index.json').then(r=>r.json()).then(d=>{idx=d;render(input.value);}).catch(()=>{resBox.innerHTML='<div class="search-empty">索引加载失败，请刷新重试</div>';});
  }
  function close(){overlay.hidden=true;document.documentElement.style.overflow='';btn.focus();}
  function move(dir){
    const items=[...resBox.querySelectorAll('a')];if(!items.length)return;
    sel=(sel+dir+items.length)%items.length;
    items.forEach((a,i)=>a.classList.toggle('sel',i===sel));
    items[sel].scrollIntoView({block:'nearest'});
  }
  function snippet(text,terms){
    const low=text.toLowerCase();
    let pos=-1;
    for(const t of terms){const i=low.indexOf(t);if(i>-1){pos=i;break;}}
    if(pos<0)return esc(text.slice(0,72))+'…';
    const a=Math.max(0,pos-32),b=Math.min(text.length,pos+56);
    let s=(a>0?'…':'')+text.slice(a,b)+(b<text.length?'…':'');
    s=esc(s);
    for(const t of terms){s=s.replace(new RegExp(rxesc(esc(t)),'gi'),m=>'<mark>'+m+'</mark>');}
    return s;
  }
  function render(q){
    sel=0;
    if(!idx){resBox.innerHTML='<div class="search-empty">正在加载索引…</div>';return;}
    const terms=q.trim().toLowerCase().split(/\s+/).filter(Boolean);
    if(!terms.length){resBox.innerHTML='<div class="search-empty">输入关键词，跨 '+idx.length+' 个页面检索</div>';results=[];return;}
    results=[];
    for(const r of idx){
      const tl=r.t.toLowerCase(),xl=r.x.toLowerCase();
      let score=0,ok=true;
      for(const t of terms){
        const inT=tl.indexOf(t)>-1;
        let n=0,i=xl.indexOf(t);
        while(i>-1&&n<6){n++;i=xl.indexOf(t,i+t.length);}
        if(!inT&&!n){ok=false;break;}
        score+=(inT?9:0)+n;
      }
      if(ok)results.push({r,score});
    }
    results.sort((a,b)=>b.score-a.score);
    results=results.slice(0,12);
    if(!results.length){resBox.innerHTML='<div class="search-empty">没有匹配「'+esc(q.trim())+'」的页面</div>';return;}
    resBox.innerHTML=results.map((it,i)=>'<a role="option" class="'+(i===0?'sel':'')+'" href="'+SITE_ROOT+it.r.u+'">'
      +'<div class="rt">'+snippet(it.r.t,terms)+'</div>'
      +'<div class="rs">'+snippet(it.r.x,terms)+'</div></a>').join('');
    [...resBox.querySelectorAll('a')].forEach((a,i)=>a.addEventListener('mousemove',()=>{sel=i;resBox.querySelectorAll('a').forEach((x,j)=>x.classList.toggle('sel',j===i));}));
  }
  btn.addEventListener('click',open);
  addEventListener('keydown',e=>{
    if((e.metaKey||e.ctrlKey)&&(e.key==='k'||e.key==='K')){e.preventDefault();overlay&&!overlay.hidden?close():open();}
    else if(e.key==='Escape'&&overlay&&!overlay.hidden)close();
    else if(e.key==='/'&&(!overlay||overlay.hidden)&&!/^(INPUT|TEXTAREA)$/.test(document.activeElement.tagName)){e.preventDefault();open();}
  });
})();
