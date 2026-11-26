import React,{useEffect,useMemo,useRef,useState} from 'react'
import cytoscape from 'cytoscape'
import {Plus,Minus,Scan,Network as Net,Focus} from 'lucide-react'
import {Panel,Empty} from './ui'
import {api,money} from './api'

export default function Network({graph,clusters,compact=false,open,onAccount,onTransaction}){
 const box=useRef(null),instance=useRef(null)
 const [group,G]=useState(''),[risk,R]=useState(''),[search,S]=useState(''),[path,P]=useState(''),[from,F]=useState(''),[to,T]=useState('')
 const nodes=useMemo(()=>{
   let filtered=graph.nodes.filter(n=>(!group||n.cluster===group)&&(!risk||n.risk===risk))
   if(compact){
     const groups=clusters.slice(0,3)
     const ids=new Set(groups.flatMap(c=>c.members.slice(0,8)))
     const ordinary=graph.nodes.filter(n=>!ids.has(n.id)).sort((a,b)=>b.count-a.count)
     if(ordinary.length){const hub=ordinary[0].id;ids.add(hub);graph.edges.filter(e=>e.source===hub||e.target===hub).slice(0,8).forEach(e=>{ids.add(e.source);ids.add(e.target)})}
     return filtered.filter(n=>ids.has(n.id))
   }
   return filtered
 },[graph,clusters,compact,group,risk])
 const handlers=useRef({});handlers.current={onAccount,onTransaction}
 useEffect(()=>{
   if(!box.current)return
   const ids=new Set(nodes.map(n=>n.id)),groups=[...new Set(nodes.map(n=>n.cluster||'ungrouped'))]
   const anchors=[[155,125],[415,90],[335,257],[640,222]]
   const buckets=Object.groupBy?Object.groupBy(nodes,n=>n.cluster||'ungrouped'):nodes.reduce((a,n)=>{(a[n.cluster||'ungrouped']??=[]).push(n);return a},{})
   const elements=nodes.map(n=>{
     const k=n.cluster||'ungrouped',i=buckets[k].indexOf(n),gi=groups.indexOf(k),v=2*Math.PI*i/buckets[k].length
     const center=anchors[gi]||[gi*150,150],radius=45+12*(i%3)
     const flagged=['High','Critical'].includes(n.risk)
     return {data:{id:n.id,label:n.id,color:flagged?'#ff6884':'#58a4ef',size:Math.min(39,19+Math.sqrt(n.count)*2)},position:{x:center[0]+Math.cos(v)*radius,y:center[1]+Math.sin(v)*radius},classes:flagged?'danger':''}
   })
   graph.edges.filter(e=>ids.has(e.source)&&ids.has(e.target)).forEach((e,i)=>elements.push({data:{id:'edge:'+i,source:e.source,target:e.target,tx:e.transactions,color:nodes.find(n=>n.id===e.source)?.cluster?'#aa546d':'#35698c'}}))
   const cy=cytoscape({container:box.current,elements,minZoom:.08,maxZoom:6,wheelSensitivity:.25,layout:compact?{name:'preset',padding:24}:{name:'cose',animate:false,randomize:true,nodeRepulsion:()=>12000,idealEdgeLength:()=>85,padding:25},style:[
     {selector:'node',style:{width:'data(size)',height:'data(size)','background-color':'data(color)','border-width':3,'border-color':'#152c44',label:'data(label)','font-size':10,color:'#b7cde0','text-margin-y':5,'text-valign':'bottom','text-outline-color':'#0b1321','text-outline-width':2}},
     {selector:'.danger',style:{'border-width':4,'border-color':'#663448','underlay-color':'#f75777','underlay-opacity':.10,'underlay-padding':6}},
     {selector:'edge',style:{width:1.3,'line-color':'data(color)','target-arrow-color':'data(color)','target-arrow-shape':'triangle','curve-style':'bezier','arrow-scale':.75}},
     {selector:'.dim',style:{opacity:.13}},{selector:'.match',style:{'border-width':4,'border-color':'#5fe5d7','line-color':'#5fe5d7','target-arrow-color':'#5fe5d7',width:3}}
   ]});instance.current=cy
   cy.on('tap','node',e=>handlers.current.onAccount(graph.nodes.find(n=>n.id===e.target.id())))
   cy.on('tap','edge',e=>handlers.current.onTransaction(e.target.data('tx')))
   const ro=new ResizeObserver(()=>{cy.resize();cy.fit(undefined,24)});ro.observe(box.current)
   return()=>{ro.disconnect();cy.destroy();instance.current=null}
 },[nodes,graph,compact])
 useEffect(()=>{const cy=instance.current;if(!cy)return;cy.elements().removeClass('dim match');if(search.trim()){const matches=cy.nodes().filter(n=>n.id().toLowerCase().includes(search.toLowerCase()));cy.elements().addClass('dim');matches.closedNeighborhood().removeClass('dim');if(matches.length)cy.fit(matches.closedNeighborhood(),55)}},[search,nodes])
 function trace(){const cy=instance.current,a=cy.getElementById(from),b=cy.getElementById(to);if(!a.length||!b.length){P('Select two visible accounts.');return}const res=cy.elements().dijkstra({root:a,directed:true});cy.elements().removeClass('match dim');if(!Number.isFinite(res.distanceTo(b))){P('No directed path in this view.');return}const route=res.pathTo(b);cy.elements().addClass('dim');route.removeClass('dim').addClass('match');cy.fit(route,45);P(route.nodes().map(n=>n.id()).join(' → '))}
 return <Panel title={compact?'Exchange network':'Account relationship graph'} sub={compact?'Connected accounts and flagged transfer links':'Select an account or transfer to inspect the evidence.'} action={compact?<button onClick={open}><Focus size={15}/>Explore</button>:null}>
 {!compact&&<div className="filters"><input placeholder="Find account ID" aria-label="Find account ID" value={search} onChange={e=>S(e.target.value)}/><select aria-label="Cluster" value={group} onChange={e=>G(e.target.value)}><option value="">All clusters</option>{clusters.map(c=><option key={c.id}>{c.id}</option>)}</select><select aria-label="Network risk" value={risk} onChange={e=>R(e.target.value)}><option value="">All risks</option>{['Low','Medium','High','Critical'].map(r=><option key={r}>{r}</option>)}</select></div>}
 <div className={'map '+(compact?'mini':'')}><div className="maplabel"><Net size={13}/> DIRECTED GRAPH</div><div ref={box} className="canvas"/>{!nodes.length&&<span className="mapempty">No matching accounts</span>}<div className="maptools">{[[Plus,1.25],[Minus,.8],[Scan,0]].map(([Icon,z])=><button key={z} aria-label={z===0?'Fit graph':z>1?'Zoom in':'Zoom out'} onClick={()=>{const c=instance.current;z?c.zoom({level:c.zoom()*z,renderedPosition:{x:c.width()/2,y:c.height()/2}}):c.fit(undefined,24)}}><Icon size={14}/></button>)}</div></div>
 <div className="mapfoot"><span><i className="dot red"/>Suspicious <i className="dot blue"/>Standard</span><small>{nodes.length} visible accounts</small></div>
 {!compact&&<div className="trace"><h3>Explore transfer path</h3><div className="filters">{[[from,F,'Source'],[to,T,'Destination']].map(([v,set,label])=><select key={label} aria-label={label} value={v} onChange={e=>set(e.target.value)}><option value="">{label}</option>{nodes.map(n=><option key={n.id}>{n.id}</option>)}</select>)}<button onClick={trace}>Trace path</button></div>{path&&<p>{path}</p>}</div>}</Panel>
}

