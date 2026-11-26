import React,{useEffect,useState} from 'react'
import {api,url,day,money} from './api'
import {Panel,Modal,Risk,Empty} from './ui'
export default function Cases({accounts,start,clear,notify}){
 const [list,L]=useState([]),[item,I]=useState(null),[creating,C]=useState(!!start),[account,A]=useState(start||accounts[0]?.id||''),[title,T]=useState(''),[notes,N]=useState(''),[status,S]=useState('Open'),[ids,E]=useState([]),[busy,B]=useState(false),[error,Err]=useState('')
 async function refresh(){L(await api('/cases'))}
 useEffect(()=>{refresh().catch(e=>Err(e.message))},[])
 function close(){I(null);C(false);clear();Err('')}
 async function open(id){try{let c=await api('/cases/'+id);I(c);N(c.notes);S(c.status);E(c.evidence);Err('')}catch(e){notify(e.message)}}
 async function save(e){e.preventDefault();B(true);Err('');try{const c=creating?await api('/cases','POST',{title,account,notes}):await api('/cases/'+item.id,'PATCH',{revision:item.revision,status,notes,evidence:ids});await refresh();C(false);clear();await open(c.id);notify(creating?'Case created':'Case saved')}catch(e){Err(e.message)}finally{B(false)}}
 return <Panel title="Investigation register" sub="Cases retain the evidence from their original analysis." action={<button className="primary" onClick={()=>{C(true);T('');N('');Err('')}}>New case</button>}>
 {!list.length?<Empty>{error||'No open investigations. Create a case to collect transaction evidence.'}</Empty>:<div className="scroll"><table><thead><tr>{['Case','Investigation','Account','Risk','Status'].map(k=><th key={k}>{k}</th>)}</tr></thead><tbody>{list.map(c=><tr key={c.id}><td><button className="link" onClick={()=>open(c.id)}>{c.id}</button></td><td>{c.title}</td><td>{c.account}</td><td><Risk value={c.risk}/></td><td>{c.status}</td></tr>)}</tbody></table></div>}
 {(creating||item)&&<Modal title={creating?'Create investigation':item.title} close={close}><form onSubmit={save}>{creating?<><label>Case title<input required minLength={3} maxLength={120} value={title} onChange={e=>T(e.target.value)}/></label><label>Account<select value={account} onChange={e=>A(e.target.value)}>{accounts.map(a=><option key={a.id}>{a.id}</option>)}</select></label></>:<><p className="mono">{item.id} · {item.account} · {item.account_detail.cluster||'Unclustered'}</p><Risk value={item.risk}/><label>Case status<select value={status} onChange={e=>S(e.target.value)}>{['Open','In review','Closed'].map(x=><option key={x}>{x}</option>)}</select></label></>}
 <label>Investigation notes<textarea maxLength={4000} rows={4} value={notes} onChange={e=>N(e.target.value)}/></label>
 {!creating&&<><h3>Timeline & evidence</h3><p>Select transfers to attach to this investigation.</p><div className="timeline">{item.timeline.map(r=><label key={r.id}><input type="checkbox" checked={ids.includes(r.id)} onChange={e=>E(e.target.checked?[...ids,r.id]:ids.filter(x=>x!==r.id))}/><span>{r.id} · {day(r.timestamp)}<small>{r.sender} → {r.receiver} · {money(r.amount)} · {r.risk}</small></span></label>)}</div></>}
 {error&&<p role="alert">{error}</p>}<div className="actions">{!creating&&<a className="button" href={url('/cases/'+item.id+'/pdf')}>Export saved PDF</a>}<button className="primary" disabled={busy}>{busy?'Saving…':creating?'Create case':'Save case'}</button></div></form></Modal>}</Panel>
}

