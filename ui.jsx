import React,{useEffect,useRef} from 'react'
import {X} from 'lucide-react'
import {colors} from './api'
export function Risk({value}){return <span className="risk" style={{'--tone':colors[value]}}><i/>{value}</span>}
export function Modal({title,close,children}){
 const ref=useRef(null)
 useEffect(()=>{const d=ref.current;d.showModal();return()=>d.close()},[])
 return <dialog ref={ref} onCancel={close} onClick={e=>{if(e.target===ref.current)close()}}><section><header><h2>{title}</h2><button aria-label="Close dialog" onClick={close}><X size={18}/></button></header>{children}</section></dialog>
}
export function Panel({title,sub,action,children,cls=''}){return <section className={'panel '+cls}><header><div><h2>{title}</h2>{sub&&<p>{sub}</p>}</div>{action}</header>{children}</section>}
export function Empty({children}){return <p className="empty">{children}</p>}

