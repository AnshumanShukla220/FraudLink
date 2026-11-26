export const url=(p)=> (import.meta.env.VITE_API_BASE || '')+'/api'+p
export async function api(path,method='GET',data){
  const isFile=data instanceof FormData
  const response=await fetch(url(path),{method,headers:data&&!isFile?{'Content-Type':'application/json'}:{},body:data?(isFile?data:JSON.stringify(data)):undefined})
  if(!response.ok){
    const detail=(await response.json().catch(()=>({}))).detail
    throw new Error(typeof detail==='string'?detail:Array.isArray(detail)?detail.map(x=>x.msg).join(', '):'Request failed ('+response.status+')')
  }
  return response.json()
}
export const fmt=n=>Number(n).toLocaleString('en-US')
export const money=n=>new Intl.NumberFormat('en-US',{style:'currency',currency:'USD',minimumFractionDigits:2,maximumFractionDigits:2}).format(n)
export const day=d=>new Date(d).toLocaleDateString('en-US',{month:'short',day:'numeric',timeZone:'UTC'})
export const colors={Critical:'#ff637d',High:'#ffac68',Medium:'#a98afd',Low:'#39cdc7'}

