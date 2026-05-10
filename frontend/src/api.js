const API_HOST =
  typeof window !== 'undefined' && window.location && window.location.hostname
    ? window.location.hostname
    : '127.0.0.1';

const BASE = `http://${API_HOST}:8000/api`;
async function req(path, opts={}){
  const res = await fetch(BASE + path, {headers:{'Content-Type':'application/json'}, ...opts});
  if(!res.ok){let t=await res.text(); try{t=JSON.parse(t).detail||t}catch{} throw new Error(t)}
  return res.json();
}
export const getJSON = p => req(p);
export const postJSON = (p, data={}) => req(p,{method:'POST',body:JSON.stringify({data})});
export const putJSON = (p, data={}) => req(p,{method:'PUT',body:JSON.stringify({data})});
export const del = p => req(p,{method:'DELETE'});
