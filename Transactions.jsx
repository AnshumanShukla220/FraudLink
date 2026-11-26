import React,{useEffect,useState} from 'react'
import {Download,Search,ChevronLeft,ChevronRight,UploadCloud} from 'lucide-react'
import {api,url,money,day,fmt} from './api'
import {Panel,Risk,Empty} from './ui'
export default function Transactions({inspect,upload,run,initial=''}){
 const [filters,S]=useState({q:initial,risk:'',minimum:'',maximum:'',start:'',end:''}),[page,P]=useState(1),[result,D]=useState(null),[err,E]=useState('')
 const params=new URLSearchParams(Object.entries({...filters,page,size:15}).filter(([k,v])=>v!==''))
 function edit(k,v){S({...filters,[k]:v});P(1)}
 useEffect(()=>{let live=true;D(null);E('');const t=setTimeout(()=>api('/transactions?'+params).then(d=>live&&D(d)).catch(e=>live&&E(e.message)),180);return()=>{live=false;clearTimeout(t)}},[params.toString(),run])
 return <Panel title="Transaction ledger" sub="Search transfers and inspect their detection evidence." action={<a className="button" href={url('/transactions?'+params+'&download=true')}><Download size={15}/>CSV</a>}>
 <div className="filters"><label className="search"><Search size={16}/><input placeholder="Transaction or account ID" value={filters.q} onChange={e=>edit('q',e.target.value)}/></label>
 <select aria-label="Risk level" value={filters.risk} onChange={e=>edit('risk',e.target.value)}><option value="">All risk levels</option>{['Critical','High','Medium','Low'].map(v=><option key={v}>{v}</option>)}</select>
 {['minimum','maximum','start','end'].map((k,i)=><label className="field" key={k}>{['Min USD','Max USD','From','Through'][i]}<input type={i<2?'number':'date'} min={i<2?'0':undefined} value={filters[k]} onChange={e=>edit(k,e.target.value)}/></label>)}</div>
 {err?<Empty>{err}</Empty>:!result?<div className="skeleton"/>:<><div className="scroll"><table><thead><tr>{['Transaction','Date (UTC)','Sender','Receiver','Amount','Risk'].map(h=><th key={h}>{h}</th>)}</tr></thead><tbody>{result.items.map(r=><tr key={r.id}><td><button className="link mono" onClick={()=>inspect(r.id)}>{r.id}</button></td><td>{day(r.timestamp)}</td><td>{r.sender}</td><td>{r.receiver}</td><td>{money(r.amount)}</td><td><Risk value={r.risk}/></td></tr>)}</tbody></table></div>{!result.total&&<Empty>No transactions match these filters.</Empty>}<footer>{fmt(result.total)} results <div><button disabled={page===1} onClick={()=>P(page-1)} aria-label="Previous page"><ChevronLeft size={15}/></button> Page {page} of {Math.max(1,Math.ceil(result.total/15))} <button disabled={page*15>=result.total} onClick={()=>P(page+1)} aria-label="Next page"><ChevronRight size={15}/></button></div></footer></>}
 </Panel>
}

