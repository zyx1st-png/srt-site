
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
