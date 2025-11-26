var rv=Object.defineProperty;var iv=(e,t,n)=>t in e?rv(e,t,{enumerable:!0,configurable:!0,writable:!0,value:n}):e[t]=n;var R=(e,t,n)=>iv(e,typeof t!="symbol"?t+"":t,n);function sv(e,t){for(var n=0;n<t.length;n++){const r=t[n];if(typeof r!="string"&&!Array.isArray(r)){for(const i in r)if(i!=="default"&&!(i in e)){const s=Object.getOwnPropertyDescriptor(r,i);s&&Object.defineProperty(e,i,s.get?s:{enumerable:!0,get:()=>r[i]})}}}return Object.freeze(Object.defineProperty(e,Symbol.toStringTag,{value:"Module"}))}(function(){const t=document.createElement("link").relList;if(t&&t.supports&&t.supports("modulepreload"))return;for(const i of document.querySelectorAll('link[rel="modulepreload"]'))r(i);new MutationObserver(i=>{for(const s of i)if(s.type==="childList")for(const a of s.addedNodes)a.tagName==="LINK"&&a.rel==="modulepreload"&&r(a)}).observe(document,{childList:!0,subtree:!0});function n(i){const s={};return i.integrity&&(s.integrity=i.integrity),i.referrerPolicy&&(s.referrerPolicy=i.referrerPolicy),i.crossOrigin==="use-credentials"?s.credentials="include":i.crossOrigin==="anonymous"?s.credentials="omit":s.credentials="same-origin",s}function r(i){if(i.ep)return;i.ep=!0;const s=n(i);fetch(i.href,s)}})();function av(e){return e&&e.__esModule&&Object.prototype.hasOwnProperty.call(e,"default")?e.default:e}var kf={exports:{}},Ya={},wf={exports:{}},F={};/**
 * @license React
 * react.production.min.js
 *
 * Copyright (c) Facebook, Inc. and its affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */var es=Symbol.for("react.element"),ov=Symbol.for("react.portal"),lv=Symbol.for("react.fragment"),cv=Symbol.for("react.strict_mode"),uv=Symbol.for("react.profiler"),dv=Symbol.for("react.provider"),hv=Symbol.for("react.context"),fv=Symbol.for("react.forward_ref"),pv=Symbol.for("react.suspense"),mv=Symbol.for("react.memo"),gv=Symbol.for("react.lazy"),Ru=Symbol.iterator;function vv(e){return e===null||typeof e!="object"?null:(e=Ru&&e[Ru]||e["@@iterator"],typeof e=="function"?e:null)}var _f={isMounted:function(){return!1},enqueueForceUpdate:function(){},enqueueReplaceState:function(){},enqueueSetState:function(){}},jf=Object.assign,Sf={};function Lr(e,t,n){this.props=e,this.context=t,this.refs=Sf,this.updater=n||_f}Lr.prototype.isReactComponent={};Lr.prototype.setState=function(e,t){if(typeof e!="object"&&typeof e!="function"&&e!=null)throw Error("setState(...): takes an object of state variables to update or a function which returns an object of state variables.");this.updater.enqueueSetState(this,e,t,"setState")};Lr.prototype.forceUpdate=function(e){this.updater.enqueueForceUpdate(this,e,"forceUpdate")};function Nf(){}Nf.prototype=Lr.prototype;function pc(e,t,n){this.props=e,this.context=t,this.refs=Sf,this.updater=n||_f}var mc=pc.prototype=new Nf;mc.constructor=pc;jf(mc,Lr.prototype);mc.isPureReactComponent=!0;var Lu=Array.isArray,Cf=Object.prototype.hasOwnProperty,gc={current:null},Mf={key:!0,ref:!0,__self:!0,__source:!0};function Pf(e,t,n){var r,i={},s=null,a=null;if(t!=null)for(r in t.ref!==void 0&&(a=t.ref),t.key!==void 0&&(s=""+t.key),t)Cf.call(t,r)&&!Mf.hasOwnProperty(r)&&(i[r]=t[r]);var o=arguments.length-2;if(o===1)i.children=n;else if(1<o){for(var l=Array(o),u=0;u<o;u++)l[u]=arguments[u+2];i.children=l}if(e&&e.defaultProps)for(r in o=e.defaultProps,o)i[r]===void 0&&(i[r]=o[r]);return{$$typeof:es,type:e,key:s,ref:a,props:i,_owner:gc.current}}function yv(e,t){return{$$typeof:es,type:e.type,key:t,ref:e.ref,props:e.props,_owner:e._owner}}function vc(e){return typeof e=="object"&&e!==null&&e.$$typeof===es}function xv(e){var t={"=":"=0",":":"=2"};return"$"+e.replace(/[=:]/g,function(n){return t[n]})}var Ou=/\/+/g;function yo(e,t){return typeof e=="object"&&e!==null&&e.key!=null?xv(""+e.key):t.toString(36)}function Vs(e,t,n,r,i){var s=typeof e;(s==="undefined"||s==="boolean")&&(e=null);var a=!1;if(e===null)a=!0;else switch(s){case"string":case"number":a=!0;break;case"object":switch(e.$$typeof){case es:case ov:a=!0}}if(a)return a=e,i=i(a),e=r===""?"."+yo(a,0):r,Lu(i)?(n="",e!=null&&(n=e.replace(Ou,"$&/")+"/"),Vs(i,t,n,"",function(u){return u})):i!=null&&(vc(i)&&(i=yv(i,n+(!i.key||a&&a.key===i.key?"":(""+i.key).replace(Ou,"$&/")+"/")+e)),t.push(i)),1;if(a=0,r=r===""?".":r+":",Lu(e))for(var o=0;o<e.length;o++){s=e[o];var l=r+yo(s,o);a+=Vs(s,t,n,l,i)}else if(l=vv(e),typeof l=="function")for(e=l.call(e),o=0;!(s=e.next()).done;)s=s.value,l=r+yo(s,o++),a+=Vs(s,t,n,l,i);else if(s==="object")throw t=String(e),Error("Objects are not valid as a React child (found: "+(t==="[object Object]"?"object with keys {"+Object.keys(e).join(", ")+"}":t)+"). If you meant to render a collection of children, use an array instead.");return a}function ps(e,t,n){if(e==null)return e;var r=[],i=0;return Vs(e,r,"","",function(s){return t.call(n,s,i++)}),r}function bv(e){if(e._status===-1){var t=e._result;t=t(),t.then(function(n){(e._status===0||e._status===-1)&&(e._status=1,e._result=n)},function(n){(e._status===0||e._status===-1)&&(e._status=2,e._result=n)}),e._status===-1&&(e._status=0,e._result=t)}if(e._status===1)return e._result.default;throw e._result}var Ie={current:null},Us={transition:null},kv={ReactCurrentDispatcher:Ie,ReactCurrentBatchConfig:Us,ReactCurrentOwner:gc};function Ef(){throw Error("act(...) is not supported in production builds of React.")}F.Children={map:ps,forEach:function(e,t,n){ps(e,function(){t.apply(this,arguments)},n)},count:function(e){var t=0;return ps(e,function(){t++}),t},toArray:function(e){return ps(e,function(t){return t})||[]},only:function(e){if(!vc(e))throw Error("React.Children.only expected to receive a single React element child.");return e}};F.Component=Lr;F.Fragment=lv;F.Profiler=uv;F.PureComponent=pc;F.StrictMode=cv;F.Suspense=pv;F.__SECRET_INTERNALS_DO_NOT_USE_OR_YOU_WILL_BE_FIRED=kv;F.act=Ef;F.cloneElement=function(e,t,n){if(e==null)throw Error("React.cloneElement(...): The argument must be a React element, but you passed "+e+".");var r=jf({},e.props),i=e.key,s=e.ref,a=e._owner;if(t!=null){if(t.ref!==void 0&&(s=t.ref,a=gc.current),t.key!==void 0&&(i=""+t.key),e.type&&e.type.defaultProps)var o=e.type.defaultProps;for(l in t)Cf.call(t,l)&&!Mf.hasOwnProperty(l)&&(r[l]=t[l]===void 0&&o!==void 0?o[l]:t[l])}var l=arguments.length-2;if(l===1)r.children=n;else if(1<l){o=Array(l);for(var u=0;u<l;u++)o[u]=arguments[u+2];r.children=o}return{$$typeof:es,type:e.type,key:i,ref:s,props:r,_owner:a}};F.createContext=function(e){return e={$$typeof:hv,_currentValue:e,_currentValue2:e,_threadCount:0,Provider:null,Consumer:null,_defaultValue:null,_globalName:null},e.Provider={$$typeof:dv,_context:e},e.Consumer=e};F.createElement=Pf;F.createFactory=function(e){var t=Pf.bind(null,e);return t.type=e,t};F.createRef=function(){return{current:null}};F.forwardRef=function(e){return{$$typeof:fv,render:e}};F.isValidElement=vc;F.lazy=function(e){return{$$typeof:gv,_payload:{_status:-1,_result:e},_init:bv}};F.memo=function(e,t){return{$$typeof:mv,type:e,compare:t===void 0?null:t}};F.startTransition=function(e){var t=Us.transition;Us.transition={};try{e()}finally{Us.transition=t}};F.unstable_act=Ef;F.useCallback=function(e,t){return Ie.current.useCallback(e,t)};F.useContext=function(e){return Ie.current.useContext(e)};F.useDebugValue=function(){};F.useDeferredValue=function(e){return Ie.current.useDeferredValue(e)};F.useEffect=function(e,t){return Ie.current.useEffect(e,t)};F.useId=function(){return Ie.current.useId()};F.useImperativeHandle=function(e,t,n){return Ie.current.useImperativeHandle(e,t,n)};F.useInsertionEffect=function(e,t){return Ie.current.useInsertionEffect(e,t)};F.useLayoutEffect=function(e,t){return Ie.current.useLayoutEffect(e,t)};F.useMemo=function(e,t){return Ie.current.useMemo(e,t)};F.useReducer=function(e,t,n){return Ie.current.useReducer(e,t,n)};F.useRef=function(e){return Ie.current.useRef(e)};F.useState=function(e){return Ie.current.useState(e)};F.useSyncExternalStore=function(e,t,n){return Ie.current.useSyncExternalStore(e,t,n)};F.useTransition=function(){return Ie.current.useTransition()};F.version="18.3.1";wf.exports=F;var _=wf.exports;const Tf=av(_),wv=sv({__proto__:null,default:Tf},[_]);/**
 * @license React
 * react-jsx-runtime.production.min.js
 *
 * Copyright (c) Facebook, Inc. and its affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */var _v=_,jv=Symbol.for("react.element"),Sv=Symbol.for("react.fragment"),Nv=Object.prototype.hasOwnProperty,Cv=_v.__SECRET_INTERNALS_DO_NOT_USE_OR_YOU_WILL_BE_FIRED.ReactCurrentOwner,Mv={key:!0,ref:!0,__self:!0,__source:!0};function zf(e,t,n){var r,i={},s=null,a=null;n!==void 0&&(s=""+n),t.key!==void 0&&(s=""+t.key),t.ref!==void 0&&(a=t.ref);for(r in t)Nv.call(t,r)&&!Mv.hasOwnProperty(r)&&(i[r]=t[r]);if(e&&e.defaultProps)for(r in t=e.defaultProps,t)i[r]===void 0&&(i[r]=t[r]);return{$$typeof:jv,type:e,key:s,ref:a,props:i,_owner:Cv.current}}Ya.Fragment=Sv;Ya.jsx=zf;Ya.jsxs=zf;kf.exports=Ya;var c=kf.exports,ll={},Df={exports:{}},Je={},Rf={exports:{}},Lf={};/**
 * @license React
 * scheduler.production.min.js
 *
 * Copyright (c) Facebook, Inc. and its affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */(function(e){function t(P,C){var D=P.length;P.push(C);e:for(;0<D;){var I=D-1>>>1,J=P[I];if(0<i(J,C))P[I]=C,P[D]=J,D=I;else break e}}function n(P){return P.length===0?null:P[0]}function r(P){if(P.length===0)return null;var C=P[0],D=P.pop();if(D!==C){P[0]=D;e:for(var I=0,J=P.length,yt=J>>>1;I<yt;){var Re=2*(I+1)-1,Ct=P[Re],Le=Re+1,fs=P[Le];if(0>i(Ct,D))Le<J&&0>i(fs,Ct)?(P[I]=fs,P[Le]=D,I=Le):(P[I]=Ct,P[Re]=D,I=Re);else if(Le<J&&0>i(fs,D))P[I]=fs,P[Le]=D,I=Le;else break e}}return C}function i(P,C){var D=P.sortIndex-C.sortIndex;return D!==0?D:P.id-C.id}if(typeof performance=="object"&&typeof performance.now=="function"){var s=performance;e.unstable_now=function(){return s.now()}}else{var a=Date,o=a.now();e.unstable_now=function(){return a.now()-o}}var l=[],u=[],d=1,h=null,f=3,p=!1,m=!1,v=!1,y=typeof setTimeout=="function"?setTimeout:null,g=typeof clearTimeout=="function"?clearTimeout:null,x=typeof setImmediate<"u"?setImmediate:null;typeof navigator<"u"&&navigator.scheduling!==void 0&&navigator.scheduling.isInputPending!==void 0&&navigator.scheduling.isInputPending.bind(navigator.scheduling);function b(P){for(var C=n(u);C!==null;){if(C.callback===null)r(u);else if(C.startTime<=P)r(u),C.sortIndex=C.expirationTime,t(l,C);else break;C=n(u)}}function k(P){if(v=!1,b(P),!m)if(n(l)!==null)m=!0,U(w);else{var C=n(u);C!==null&&K(k,C.startTime-P)}}function w(P,C){m=!1,v&&(v=!1,g(N),N=-1),p=!0;var D=f;try{for(b(C),h=n(l);h!==null&&(!(h.expirationTime>C)||P&&!L());){var I=h.callback;if(typeof I=="function"){h.callback=null,f=h.priorityLevel;var J=I(h.expirationTime<=C);C=e.unstable_now(),typeof J=="function"?h.callback=J:h===n(l)&&r(l),b(C)}else r(l);h=n(l)}if(h!==null)var yt=!0;else{var Re=n(u);Re!==null&&K(k,Re.startTime-C),yt=!1}return yt}finally{h=null,f=D,p=!1}}var j=!1,S=null,N=-1,T=5,E=-1;function L(){return!(e.unstable_now()-E<T)}function A(){if(S!==null){var P=e.unstable_now();E=P;var C=!0;try{C=S(!0,P)}finally{C?q():(j=!1,S=null)}}else j=!1}var q;if(typeof x=="function")q=function(){x(A)};else if(typeof MessageChannel<"u"){var ve=new MessageChannel,W=ve.port2;ve.port1.onmessage=A,q=function(){W.postMessage(null)}}else q=function(){y(A,0)};function U(P){S=P,j||(j=!0,q())}function K(P,C){N=y(function(){P(e.unstable_now())},C)}e.unstable_IdlePriority=5,e.unstable_ImmediatePriority=1,e.unstable_LowPriority=4,e.unstable_NormalPriority=3,e.unstable_Profiling=null,e.unstable_UserBlockingPriority=2,e.unstable_cancelCallback=function(P){P.callback=null},e.unstable_continueExecution=function(){m||p||(m=!0,U(w))},e.unstable_forceFrameRate=function(P){0>P||125<P?console.error("forceFrameRate takes a positive int between 0 and 125, forcing frame rates higher than 125 fps is not supported"):T=0<P?Math.floor(1e3/P):5},e.unstable_getCurrentPriorityLevel=function(){return f},e.unstable_getFirstCallbackNode=function(){return n(l)},e.unstable_next=function(P){switch(f){case 1:case 2:case 3:var C=3;break;default:C=f}var D=f;f=C;try{return P()}finally{f=D}},e.unstable_pauseExecution=function(){},e.unstable_requestPaint=function(){},e.unstable_runWithPriority=function(P,C){switch(P){case 1:case 2:case 3:case 4:case 5:break;default:P=3}var D=f;f=P;try{return C()}finally{f=D}},e.unstable_scheduleCallback=function(P,C,D){var I=e.unstable_now();switch(typeof D=="object"&&D!==null?(D=D.delay,D=typeof D=="number"&&0<D?I+D:I):D=I,P){case 1:var J=-1;break;case 2:J=250;break;case 5:J=1073741823;break;case 4:J=1e4;break;default:J=5e3}return J=D+J,P={id:d++,callback:C,priorityLevel:P,startTime:D,expirationTime:J,sortIndex:-1},D>I?(P.sortIndex=D,t(u,P),n(l)===null&&P===n(u)&&(v?(g(N),N=-1):v=!0,K(k,D-I))):(P.sortIndex=J,t(l,P),m||p||(m=!0,U(w))),P},e.unstable_shouldYield=L,e.unstable_wrapCallback=function(P){var C=f;return function(){var D=f;f=C;try{return P.apply(this,arguments)}finally{f=D}}}})(Lf);Rf.exports=Lf;var Pv=Rf.exports;/**
 * @license React
 * react-dom.production.min.js
 *
 * Copyright (c) Facebook, Inc. and its affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */var Ev=_,qe=Pv;function M(e){for(var t="https://reactjs.org/docs/error-decoder.html?invariant="+e,n=1;n<arguments.length;n++)t+="&args[]="+encodeURIComponent(arguments[n]);return"Minified React error #"+e+"; visit "+t+" for the full message or use the non-minified dev environment for full errors and additional helpful warnings."}var Of=new Set,Ni={};function Qn(e,t){jr(e,t),jr(e+"Capture",t)}function jr(e,t){for(Ni[e]=t,e=0;e<t.length;e++)Of.add(t[e])}var Ft=!(typeof window>"u"||typeof window.document>"u"||typeof window.document.createElement>"u"),cl=Object.prototype.hasOwnProperty,Tv=/^[:A-Z_a-z\u00C0-\u00D6\u00D8-\u00F6\u00F8-\u02FF\u0370-\u037D\u037F-\u1FFF\u200C-\u200D\u2070-\u218F\u2C00-\u2FEF\u3001-\uD7FF\uF900-\uFDCF\uFDF0-\uFFFD][:A-Z_a-z\u00C0-\u00D6\u00D8-\u00F6\u00F8-\u02FF\u0370-\u037D\u037F-\u1FFF\u200C-\u200D\u2070-\u218F\u2C00-\u2FEF\u3001-\uD7FF\uF900-\uFDCF\uFDF0-\uFFFD\-.0-9\u00B7\u0300-\u036F\u203F-\u2040]*$/,Au={},Iu={};function zv(e){return cl.call(Iu,e)?!0:cl.call(Au,e)?!1:Tv.test(e)?Iu[e]=!0:(Au[e]=!0,!1)}function Dv(e,t,n,r){if(n!==null&&n.type===0)return!1;switch(typeof t){case"function":case"symbol":return!0;case"boolean":return r?!1:n!==null?!n.acceptsBooleans:(e=e.toLowerCase().slice(0,5),e!=="data-"&&e!=="aria-");default:return!1}}function Rv(e,t,n,r){if(t===null||typeof t>"u"||Dv(e,t,n,r))return!0;if(r)return!1;if(n!==null)switch(n.type){case 3:return!t;case 4:return t===!1;case 5:return isNaN(t);case 6:return isNaN(t)||1>t}return!1}function Fe(e,t,n,r,i,s,a){this.acceptsBooleans=t===2||t===3||t===4,this.attributeName=r,this.attributeNamespace=i,this.mustUseProperty=n,this.propertyName=e,this.type=t,this.sanitizeURL=s,this.removeEmptyString=a}var je={};"children dangerouslySetInnerHTML defaultValue defaultChecked innerHTML suppressContentEditableWarning suppressHydrationWarning style".split(" ").forEach(function(e){je[e]=new Fe(e,0,!1,e,null,!1,!1)});[["acceptCharset","accept-charset"],["className","class"],["htmlFor","for"],["httpEquiv","http-equiv"]].forEach(function(e){var t=e[0];je[t]=new Fe(t,1,!1,e[1],null,!1,!1)});["contentEditable","draggable","spellCheck","value"].forEach(function(e){je[e]=new Fe(e,2,!1,e.toLowerCase(),null,!1,!1)});["autoReverse","externalResourcesRequired","focusable","preserveAlpha"].forEach(function(e){je[e]=new Fe(e,2,!1,e,null,!1,!1)});"allowFullScreen async autoFocus autoPlay controls default defer disabled disablePictureInPicture disableRemotePlayback formNoValidate hidden loop noModule noValidate open playsInline readOnly required reversed scoped seamless itemScope".split(" ").forEach(function(e){je[e]=new Fe(e,3,!1,e.toLowerCase(),null,!1,!1)});["checked","multiple","muted","selected"].forEach(function(e){je[e]=new Fe(e,3,!0,e,null,!1,!1)});["capture","download"].forEach(function(e){je[e]=new Fe(e,4,!1,e,null,!1,!1)});["cols","rows","size","span"].forEach(function(e){je[e]=new Fe(e,6,!1,e,null,!1,!1)});["rowSpan","start"].forEach(function(e){je[e]=new Fe(e,5,!1,e.toLowerCase(),null,!1,!1)});var yc=/[\-:]([a-z])/g;function xc(e){return e[1].toUpperCase()}"accent-height alignment-baseline arabic-form baseline-shift cap-height clip-path clip-rule color-interpolation color-interpolation-filters color-profile color-rendering dominant-baseline enable-background fill-opacity fill-rule flood-color flood-opacity font-family font-size font-size-adjust font-stretch font-style font-variant font-weight glyph-name glyph-orientation-horizontal glyph-orientation-vertical horiz-adv-x horiz-origin-x image-rendering letter-spacing lighting-color marker-end marker-mid marker-start overline-position overline-thickness paint-order panose-1 pointer-events rendering-intent shape-rendering stop-color stop-opacity strikethrough-position strikethrough-thickness stroke-dasharray stroke-dashoffset stroke-linecap stroke-linejoin stroke-miterlimit stroke-opacity stroke-width text-anchor text-decoration text-rendering underline-position underline-thickness unicode-bidi unicode-range units-per-em v-alphabetic v-hanging v-ideographic v-mathematical vector-effect vert-adv-y vert-origin-x vert-origin-y word-spacing writing-mode xmlns:xlink x-height".split(" ").forEach(function(e){var t=e.replace(yc,xc);je[t]=new Fe(t,1,!1,e,null,!1,!1)});"xlink:actuate xlink:arcrole xlink:role xlink:show xlink:title xlink:type".split(" ").forEach(function(e){var t=e.replace(yc,xc);je[t]=new Fe(t,1,!1,e,"http://www.w3.org/1999/xlink",!1,!1)});["xml:base","xml:lang","xml:space"].forEach(function(e){var t=e.replace(yc,xc);je[t]=new Fe(t,1,!1,e,"http://www.w3.org/XML/1998/namespace",!1,!1)});["tabIndex","crossOrigin"].forEach(function(e){je[e]=new Fe(e,1,!1,e.toLowerCase(),null,!1,!1)});je.xlinkHref=new Fe("xlinkHref",1,!1,"xlink:href","http://www.w3.org/1999/xlink",!0,!1);["src","href","action","formAction"].forEach(function(e){je[e]=new Fe(e,1,!1,e.toLowerCase(),null,!0,!0)});function bc(e,t,n,r){var i=je.hasOwnProperty(t)?je[t]:null;(i!==null?i.type!==0:r||!(2<t.length)||t[0]!=="o"&&t[0]!=="O"||t[1]!=="n"&&t[1]!=="N")&&(Rv(t,n,i,r)&&(n=null),r||i===null?zv(t)&&(n===null?e.removeAttribute(t):e.setAttribute(t,""+n)):i.mustUseProperty?e[i.propertyName]=n===null?i.type===3?!1:"":n:(t=i.attributeName,r=i.attributeNamespace,n===null?e.removeAttribute(t):(i=i.type,n=i===3||i===4&&n===!0?"":""+n,r?e.setAttributeNS(r,t,n):e.setAttribute(t,n))))}var Wt=Ev.__SECRET_INTERNALS_DO_NOT_USE_OR_YOU_WILL_BE_FIRED,ms=Symbol.for("react.element"),nr=Symbol.for("react.portal"),rr=Symbol.for("react.fragment"),kc=Symbol.for("react.strict_mode"),ul=Symbol.for("react.profiler"),Af=Symbol.for("react.provider"),If=Symbol.for("react.context"),wc=Symbol.for("react.forward_ref"),dl=Symbol.for("react.suspense"),hl=Symbol.for("react.suspense_list"),_c=Symbol.for("react.memo"),Xt=Symbol.for("react.lazy"),Ff=Symbol.for("react.offscreen"),Fu=Symbol.iterator;function Vr(e){return e===null||typeof e!="object"?null:(e=Fu&&e[Fu]||e["@@iterator"],typeof e=="function"?e:null)}var ae=Object.assign,xo;function ri(e){if(xo===void 0)try{throw Error()}catch(n){var t=n.stack.trim().match(/\n( *(at )?)/);xo=t&&t[1]||""}return`
`+xo+e}var bo=!1;function ko(e,t){if(!e||bo)return"";bo=!0;var n=Error.prepareStackTrace;Error.prepareStackTrace=void 0;try{if(t)if(t=function(){throw Error()},Object.defineProperty(t.prototype,"props",{set:function(){throw Error()}}),typeof Reflect=="object"&&Reflect.construct){try{Reflect.construct(t,[])}catch(u){var r=u}Reflect.construct(e,[],t)}else{try{t.call()}catch(u){r=u}e.call(t.prototype)}else{try{throw Error()}catch(u){r=u}e()}}catch(u){if(u&&r&&typeof u.stack=="string"){for(var i=u.stack.split(`
`),s=r.stack.split(`
`),a=i.length-1,o=s.length-1;1<=a&&0<=o&&i[a]!==s[o];)o--;for(;1<=a&&0<=o;a--,o--)if(i[a]!==s[o]){if(a!==1||o!==1)do if(a--,o--,0>o||i[a]!==s[o]){var l=`
`+i[a].replace(" at new "," at ");return e.displayName&&l.includes("<anonymous>")&&(l=l.replace("<anonymous>",e.displayName)),l}while(1<=a&&0<=o);break}}}finally{bo=!1,Error.prepareStackTrace=n}return(e=e?e.displayName||e.name:"")?ri(e):""}function Lv(e){switch(e.tag){case 5:return ri(e.type);case 16:return ri("Lazy");case 13:return ri("Suspense");case 19:return ri("SuspenseList");case 0:case 2:case 15:return e=ko(e.type,!1),e;case 11:return e=ko(e.type.render,!1),e;case 1:return e=ko(e.type,!0),e;default:return""}}function fl(e){if(e==null)return null;if(typeof e=="function")return e.displayName||e.name||null;if(typeof e=="string")return e;switch(e){case rr:return"Fragment";case nr:return"Portal";case ul:return"Profiler";case kc:return"StrictMode";case dl:return"Suspense";case hl:return"SuspenseList"}if(typeof e=="object")switch(e.$$typeof){case If:return(e.displayName||"Context")+".Consumer";case Af:return(e._context.displayName||"Context")+".Provider";case wc:var t=e.render;return e=e.displayName,e||(e=t.displayName||t.name||"",e=e!==""?"ForwardRef("+e+")":"ForwardRef"),e;case _c:return t=e.displayName||null,t!==null?t:fl(e.type)||"Memo";case Xt:t=e._payload,e=e._init;try{return fl(e(t))}catch{}}return null}function Ov(e){var t=e.type;switch(e.tag){case 24:return"Cache";case 9:return(t.displayName||"Context")+".Consumer";case 10:return(t._context.displayName||"Context")+".Provider";case 18:return"DehydratedFragment";case 11:return e=t.render,e=e.displayName||e.name||"",t.displayName||(e!==""?"ForwardRef("+e+")":"ForwardRef");case 7:return"Fragment";case 5:return t;case 4:return"Portal";case 3:return"Root";case 6:return"Text";case 16:return fl(t);case 8:return t===kc?"StrictMode":"Mode";case 22:return"Offscreen";case 12:return"Profiler";case 21:return"Scope";case 13:return"Suspense";case 19:return"SuspenseList";case 25:return"TracingMarker";case 1:case 0:case 17:case 2:case 14:case 15:if(typeof t=="function")return t.displayName||t.name||null;if(typeof t=="string")return t}return null}function pn(e){switch(typeof e){case"boolean":case"number":case"string":case"undefined":return e;case"object":return e;default:return""}}function Bf(e){var t=e.type;return(e=e.nodeName)&&e.toLowerCase()==="input"&&(t==="checkbox"||t==="radio")}function Av(e){var t=Bf(e)?"checked":"value",n=Object.getOwnPropertyDescriptor(e.constructor.prototype,t),r=""+e[t];if(!e.hasOwnProperty(t)&&typeof n<"u"&&typeof n.get=="function"&&typeof n.set=="function"){var i=n.get,s=n.set;return Object.defineProperty(e,t,{configurable:!0,get:function(){return i.call(this)},set:function(a){r=""+a,s.call(this,a)}}),Object.defineProperty(e,t,{enumerable:n.enumerable}),{getValue:function(){return r},setValue:function(a){r=""+a},stopTracking:function(){e._valueTracker=null,delete e[t]}}}}function gs(e){e._valueTracker||(e._valueTracker=Av(e))}function $f(e){if(!e)return!1;var t=e._valueTracker;if(!t)return!0;var n=t.getValue(),r="";return e&&(r=Bf(e)?e.checked?"true":"false":e.value),e=r,e!==n?(t.setValue(e),!0):!1}function la(e){if(e=e||(typeof document<"u"?document:void 0),typeof e>"u")return null;try{return e.activeElement||e.body}catch{return e.body}}function pl(e,t){var n=t.checked;return ae({},t,{defaultChecked:void 0,defaultValue:void 0,value:void 0,checked:n??e._wrapperState.initialChecked})}function Bu(e,t){var n=t.defaultValue==null?"":t.defaultValue,r=t.checked!=null?t.checked:t.defaultChecked;n=pn(t.value!=null?t.value:n),e._wrapperState={initialChecked:r,initialValue:n,controlled:t.type==="checkbox"||t.type==="radio"?t.checked!=null:t.value!=null}}function Hf(e,t){t=t.checked,t!=null&&bc(e,"checked",t,!1)}function ml(e,t){Hf(e,t);var n=pn(t.value),r=t.type;if(n!=null)r==="number"?(n===0&&e.value===""||e.value!=n)&&(e.value=""+n):e.value!==""+n&&(e.value=""+n);else if(r==="submit"||r==="reset"){e.removeAttribute("value");return}t.hasOwnProperty("value")?gl(e,t.type,n):t.hasOwnProperty("defaultValue")&&gl(e,t.type,pn(t.defaultValue)),t.checked==null&&t.defaultChecked!=null&&(e.defaultChecked=!!t.defaultChecked)}function $u(e,t,n){if(t.hasOwnProperty("value")||t.hasOwnProperty("defaultValue")){var r=t.type;if(!(r!=="submit"&&r!=="reset"||t.value!==void 0&&t.value!==null))return;t=""+e._wrapperState.initialValue,n||t===e.value||(e.value=t),e.defaultValue=t}n=e.name,n!==""&&(e.name=""),e.defaultChecked=!!e._wrapperState.initialChecked,n!==""&&(e.name=n)}function gl(e,t,n){(t!=="number"||la(e.ownerDocument)!==e)&&(n==null?e.defaultValue=""+e._wrapperState.initialValue:e.defaultValue!==""+n&&(e.defaultValue=""+n))}var ii=Array.isArray;function pr(e,t,n,r){if(e=e.options,t){t={};for(var i=0;i<n.length;i++)t["$"+n[i]]=!0;for(n=0;n<e.length;n++)i=t.hasOwnProperty("$"+e[n].value),e[n].selected!==i&&(e[n].selected=i),i&&r&&(e[n].defaultSelected=!0)}else{for(n=""+pn(n),t=null,i=0;i<e.length;i++){if(e[i].value===n){e[i].selected=!0,r&&(e[i].defaultSelected=!0);return}t!==null||e[i].disabled||(t=e[i])}t!==null&&(t.selected=!0)}}function vl(e,t){if(t.dangerouslySetInnerHTML!=null)throw Error(M(91));return ae({},t,{value:void 0,defaultValue:void 0,children:""+e._wrapperState.initialValue})}function Hu(e,t){var n=t.value;if(n==null){if(n=t.children,t=t.defaultValue,n!=null){if(t!=null)throw Error(M(92));if(ii(n)){if(1<n.length)throw Error(M(93));n=n[0]}t=n}t==null&&(t=""),n=t}e._wrapperState={initialValue:pn(n)}}function Wf(e,t){var n=pn(t.value),r=pn(t.defaultValue);n!=null&&(n=""+n,n!==e.value&&(e.value=n),t.defaultValue==null&&e.defaultValue!==n&&(e.defaultValue=n)),r!=null&&(e.defaultValue=""+r)}function Wu(e){var t=e.textContent;t===e._wrapperState.initialValue&&t!==""&&t!==null&&(e.value=t)}function Vf(e){switch(e){case"svg":return"http://www.w3.org/2000/svg";case"math":return"http://www.w3.org/1998/Math/MathML";default:return"http://www.w3.org/1999/xhtml"}}function yl(e,t){return e==null||e==="http://www.w3.org/1999/xhtml"?Vf(t):e==="http://www.w3.org/2000/svg"&&t==="foreignObject"?"http://www.w3.org/1999/xhtml":e}var vs,Uf=function(e){return typeof MSApp<"u"&&MSApp.execUnsafeLocalFunction?function(t,n,r,i){MSApp.execUnsafeLocalFunction(function(){return e(t,n,r,i)})}:e}(function(e,t){if(e.namespaceURI!=="http://www.w3.org/2000/svg"||"innerHTML"in e)e.innerHTML=t;else{for(vs=vs||document.createElement("div"),vs.innerHTML="<svg>"+t.valueOf().toString()+"</svg>",t=vs.firstChild;e.firstChild;)e.removeChild(e.firstChild);for(;t.firstChild;)e.appendChild(t.firstChild)}});function Ci(e,t){if(t){var n=e.firstChild;if(n&&n===e.lastChild&&n.nodeType===3){n.nodeValue=t;return}}e.textContent=t}var hi={animationIterationCount:!0,aspectRatio:!0,borderImageOutset:!0,borderImageSlice:!0,borderImageWidth:!0,boxFlex:!0,boxFlexGroup:!0,boxOrdinalGroup:!0,columnCount:!0,columns:!0,flex:!0,flexGrow:!0,flexPositive:!0,flexShrink:!0,flexNegative:!0,flexOrder:!0,gridArea:!0,gridRow:!0,gridRowEnd:!0,gridRowSpan:!0,gridRowStart:!0,gridColumn:!0,gridColumnEnd:!0,gridColumnSpan:!0,gridColumnStart:!0,fontWeight:!0,lineClamp:!0,lineHeight:!0,opacity:!0,order:!0,orphans:!0,tabSize:!0,widows:!0,zIndex:!0,zoom:!0,fillOpacity:!0,floodOpacity:!0,stopOpacity:!0,strokeDasharray:!0,strokeDashoffset:!0,strokeMiterlimit:!0,strokeOpacity:!0,strokeWidth:!0},Iv=["Webkit","ms","Moz","O"];Object.keys(hi).forEach(function(e){Iv.forEach(function(t){t=t+e.charAt(0).toUpperCase()+e.substring(1),hi[t]=hi[e]})});function Yf(e,t,n){return t==null||typeof t=="boolean"||t===""?"":n||typeof t!="number"||t===0||hi.hasOwnProperty(e)&&hi[e]?(""+t).trim():t+"px"}function Xf(e,t){e=e.style;for(var n in t)if(t.hasOwnProperty(n)){var r=n.indexOf("--")===0,i=Yf(n,t[n],r);n==="float"&&(n="cssFloat"),r?e.setProperty(n,i):e[n]=i}}var Fv=ae({menuitem:!0},{area:!0,base:!0,br:!0,col:!0,embed:!0,hr:!0,img:!0,input:!0,keygen:!0,link:!0,meta:!0,param:!0,source:!0,track:!0,wbr:!0});function xl(e,t){if(t){if(Fv[e]&&(t.children!=null||t.dangerouslySetInnerHTML!=null))throw Error(M(137,e));if(t.dangerouslySetInnerHTML!=null){if(t.children!=null)throw Error(M(60));if(typeof t.dangerouslySetInnerHTML!="object"||!("__html"in t.dangerouslySetInnerHTML))throw Error(M(61))}if(t.style!=null&&typeof t.style!="object")throw Error(M(62))}}function bl(e,t){if(e.indexOf("-")===-1)return typeof t.is=="string";switch(e){case"annotation-xml":case"color-profile":case"font-face":case"font-face-src":case"font-face-uri":case"font-face-format":case"font-face-name":case"missing-glyph":return!1;default:return!0}}var kl=null;function jc(e){return e=e.target||e.srcElement||window,e.correspondingUseElement&&(e=e.correspondingUseElement),e.nodeType===3?e.parentNode:e}var wl=null,mr=null,gr=null;function Vu(e){if(e=rs(e)){if(typeof wl!="function")throw Error(M(280));var t=e.stateNode;t&&(t=Za(t),wl(e.stateNode,e.type,t))}}function Kf(e){mr?gr?gr.push(e):gr=[e]:mr=e}function Qf(){if(mr){var e=mr,t=gr;if(gr=mr=null,Vu(e),t)for(e=0;e<t.length;e++)Vu(t[e])}}function Gf(e,t){return e(t)}function Zf(){}var wo=!1;function qf(e,t,n){if(wo)return e(t,n);wo=!0;try{return Gf(e,t,n)}finally{wo=!1,(mr!==null||gr!==null)&&(Zf(),Qf())}}function Mi(e,t){var n=e.stateNode;if(n===null)return null;var r=Za(n);if(r===null)return null;n=r[t];e:switch(t){case"onClick":case"onClickCapture":case"onDoubleClick":case"onDoubleClickCapture":case"onMouseDown":case"onMouseDownCapture":case"onMouseMove":case"onMouseMoveCapture":case"onMouseUp":case"onMouseUpCapture":case"onMouseEnter":(r=!r.disabled)||(e=e.type,r=!(e==="button"||e==="input"||e==="select"||e==="textarea")),e=!r;break e;default:e=!1}if(e)return null;if(n&&typeof n!="function")throw Error(M(231,t,typeof n));return n}var _l=!1;if(Ft)try{var Ur={};Object.defineProperty(Ur,"passive",{get:function(){_l=!0}}),window.addEventListener("test",Ur,Ur),window.removeEventListener("test",Ur,Ur)}catch{_l=!1}function Bv(e,t,n,r,i,s,a,o,l){var u=Array.prototype.slice.call(arguments,3);try{t.apply(n,u)}catch(d){this.onError(d)}}var fi=!1,ca=null,ua=!1,jl=null,$v={onError:function(e){fi=!0,ca=e}};function Hv(e,t,n,r,i,s,a,o,l){fi=!1,ca=null,Bv.apply($v,arguments)}function Wv(e,t,n,r,i,s,a,o,l){if(Hv.apply(this,arguments),fi){if(fi){var u=ca;fi=!1,ca=null}else throw Error(M(198));ua||(ua=!0,jl=u)}}function Gn(e){var t=e,n=e;if(e.alternate)for(;t.return;)t=t.return;else{e=t;do t=e,t.flags&4098&&(n=t.return),e=t.return;while(e)}return t.tag===3?n:null}function Jf(e){if(e.tag===13){var t=e.memoizedState;if(t===null&&(e=e.alternate,e!==null&&(t=e.memoizedState)),t!==null)return t.dehydrated}return null}function Uu(e){if(Gn(e)!==e)throw Error(M(188))}function Vv(e){var t=e.alternate;if(!t){if(t=Gn(e),t===null)throw Error(M(188));return t!==e?null:e}for(var n=e,r=t;;){var i=n.return;if(i===null)break;var s=i.alternate;if(s===null){if(r=i.return,r!==null){n=r;continue}break}if(i.child===s.child){for(s=i.child;s;){if(s===n)return Uu(i),e;if(s===r)return Uu(i),t;s=s.sibling}throw Error(M(188))}if(n.return!==r.return)n=i,r=s;else{for(var a=!1,o=i.child;o;){if(o===n){a=!0,n=i,r=s;break}if(o===r){a=!0,r=i,n=s;break}o=o.sibling}if(!a){for(o=s.child;o;){if(o===n){a=!0,n=s,r=i;break}if(o===r){a=!0,r=s,n=i;break}o=o.sibling}if(!a)throw Error(M(189))}}if(n.alternate!==r)throw Error(M(190))}if(n.tag!==3)throw Error(M(188));return n.stateNode.current===n?e:t}function ep(e){return e=Vv(e),e!==null?tp(e):null}function tp(e){if(e.tag===5||e.tag===6)return e;for(e=e.child;e!==null;){var t=tp(e);if(t!==null)return t;e=e.sibling}return null}var np=qe.unstable_scheduleCallback,Yu=qe.unstable_cancelCallback,Uv=qe.unstable_shouldYield,Yv=qe.unstable_requestPaint,ce=qe.unstable_now,Xv=qe.unstable_getCurrentPriorityLevel,Sc=qe.unstable_ImmediatePriority,rp=qe.unstable_UserBlockingPriority,da=qe.unstable_NormalPriority,Kv=qe.unstable_LowPriority,ip=qe.unstable_IdlePriority,Xa=null,St=null;function Qv(e){if(St&&typeof St.onCommitFiberRoot=="function")try{St.onCommitFiberRoot(Xa,e,void 0,(e.current.flags&128)===128)}catch{}}var pt=Math.clz32?Math.clz32:qv,Gv=Math.log,Zv=Math.LN2;function qv(e){return e>>>=0,e===0?32:31-(Gv(e)/Zv|0)|0}var ys=64,xs=4194304;function si(e){switch(e&-e){case 1:return 1;case 2:return 2;case 4:return 4;case 8:return 8;case 16:return 16;case 32:return 32;case 64:case 128:case 256:case 512:case 1024:case 2048:case 4096:case 8192:case 16384:case 32768:case 65536:case 131072:case 262144:case 524288:case 1048576:case 2097152:return e&4194240;case 4194304:case 8388608:case 16777216:case 33554432:case 67108864:return e&130023424;case 134217728:return 134217728;case 268435456:return 268435456;case 536870912:return 536870912;case 1073741824:return 1073741824;default:return e}}function ha(e,t){var n=e.pendingLanes;if(n===0)return 0;var r=0,i=e.suspendedLanes,s=e.pingedLanes,a=n&268435455;if(a!==0){var o=a&~i;o!==0?r=si(o):(s&=a,s!==0&&(r=si(s)))}else a=n&~i,a!==0?r=si(a):s!==0&&(r=si(s));if(r===0)return 0;if(t!==0&&t!==r&&!(t&i)&&(i=r&-r,s=t&-t,i>=s||i===16&&(s&4194240)!==0))return t;if(r&4&&(r|=n&16),t=e.entangledLanes,t!==0)for(e=e.entanglements,t&=r;0<t;)n=31-pt(t),i=1<<n,r|=e[n],t&=~i;return r}function Jv(e,t){switch(e){case 1:case 2:case 4:return t+250;case 8:case 16:case 32:case 64:case 128:case 256:case 512:case 1024:case 2048:case 4096:case 8192:case 16384:case 32768:case 65536:case 131072:case 262144:case 524288:case 1048576:case 2097152:return t+5e3;case 4194304:case 8388608:case 16777216:case 33554432:case 67108864:return-1;case 134217728:case 268435456:case 536870912:case 1073741824:return-1;default:return-1}}function ey(e,t){for(var n=e.suspendedLanes,r=e.pingedLanes,i=e.expirationTimes,s=e.pendingLanes;0<s;){var a=31-pt(s),o=1<<a,l=i[a];l===-1?(!(o&n)||o&r)&&(i[a]=Jv(o,t)):l<=t&&(e.expiredLanes|=o),s&=~o}}function Sl(e){return e=e.pendingLanes&-1073741825,e!==0?e:e&1073741824?1073741824:0}function sp(){var e=ys;return ys<<=1,!(ys&4194240)&&(ys=64),e}function _o(e){for(var t=[],n=0;31>n;n++)t.push(e);return t}function ts(e,t,n){e.pendingLanes|=t,t!==536870912&&(e.suspendedLanes=0,e.pingedLanes=0),e=e.eventTimes,t=31-pt(t),e[t]=n}function ty(e,t){var n=e.pendingLanes&~t;e.pendingLanes=t,e.suspendedLanes=0,e.pingedLanes=0,e.expiredLanes&=t,e.mutableReadLanes&=t,e.entangledLanes&=t,t=e.entanglements;var r=e.eventTimes;for(e=e.expirationTimes;0<n;){var i=31-pt(n),s=1<<i;t[i]=0,r[i]=-1,e[i]=-1,n&=~s}}function Nc(e,t){var n=e.entangledLanes|=t;for(e=e.entanglements;n;){var r=31-pt(n),i=1<<r;i&t|e[r]&t&&(e[r]|=t),n&=~i}}var X=0;function ap(e){return e&=-e,1<e?4<e?e&268435455?16:536870912:4:1}var op,Cc,lp,cp,up,Nl=!1,bs=[],sn=null,an=null,on=null,Pi=new Map,Ei=new Map,Qt=[],ny="mousedown mouseup touchcancel touchend touchstart auxclick dblclick pointercancel pointerdown pointerup dragend dragstart drop compositionend compositionstart keydown keypress keyup input textInput copy cut paste click change contextmenu reset submit".split(" ");function Xu(e,t){switch(e){case"focusin":case"focusout":sn=null;break;case"dragenter":case"dragleave":an=null;break;case"mouseover":case"mouseout":on=null;break;case"pointerover":case"pointerout":Pi.delete(t.pointerId);break;case"gotpointercapture":case"lostpointercapture":Ei.delete(t.pointerId)}}function Yr(e,t,n,r,i,s){return e===null||e.nativeEvent!==s?(e={blockedOn:t,domEventName:n,eventSystemFlags:r,nativeEvent:s,targetContainers:[i]},t!==null&&(t=rs(t),t!==null&&Cc(t)),e):(e.eventSystemFlags|=r,t=e.targetContainers,i!==null&&t.indexOf(i)===-1&&t.push(i),e)}function ry(e,t,n,r,i){switch(t){case"focusin":return sn=Yr(sn,e,t,n,r,i),!0;case"dragenter":return an=Yr(an,e,t,n,r,i),!0;case"mouseover":return on=Yr(on,e,t,n,r,i),!0;case"pointerover":var s=i.pointerId;return Pi.set(s,Yr(Pi.get(s)||null,e,t,n,r,i)),!0;case"gotpointercapture":return s=i.pointerId,Ei.set(s,Yr(Ei.get(s)||null,e,t,n,r,i)),!0}return!1}function dp(e){var t=Pn(e.target);if(t!==null){var n=Gn(t);if(n!==null){if(t=n.tag,t===13){if(t=Jf(n),t!==null){e.blockedOn=t,up(e.priority,function(){lp(n)});return}}else if(t===3&&n.stateNode.current.memoizedState.isDehydrated){e.blockedOn=n.tag===3?n.stateNode.containerInfo:null;return}}}e.blockedOn=null}function Ys(e){if(e.blockedOn!==null)return!1;for(var t=e.targetContainers;0<t.length;){var n=Cl(e.domEventName,e.eventSystemFlags,t[0],e.nativeEvent);if(n===null){n=e.nativeEvent;var r=new n.constructor(n.type,n);kl=r,n.target.dispatchEvent(r),kl=null}else return t=rs(n),t!==null&&Cc(t),e.blockedOn=n,!1;t.shift()}return!0}function Ku(e,t,n){Ys(e)&&n.delete(t)}function iy(){Nl=!1,sn!==null&&Ys(sn)&&(sn=null),an!==null&&Ys(an)&&(an=null),on!==null&&Ys(on)&&(on=null),Pi.forEach(Ku),Ei.forEach(Ku)}function Xr(e,t){e.blockedOn===t&&(e.blockedOn=null,Nl||(Nl=!0,qe.unstable_scheduleCallback(qe.unstable_NormalPriority,iy)))}function Ti(e){function t(i){return Xr(i,e)}if(0<bs.length){Xr(bs[0],e);for(var n=1;n<bs.length;n++){var r=bs[n];r.blockedOn===e&&(r.blockedOn=null)}}for(sn!==null&&Xr(sn,e),an!==null&&Xr(an,e),on!==null&&Xr(on,e),Pi.forEach(t),Ei.forEach(t),n=0;n<Qt.length;n++)r=Qt[n],r.blockedOn===e&&(r.blockedOn=null);for(;0<Qt.length&&(n=Qt[0],n.blockedOn===null);)dp(n),n.blockedOn===null&&Qt.shift()}var vr=Wt.ReactCurrentBatchConfig,fa=!0;function sy(e,t,n,r){var i=X,s=vr.transition;vr.transition=null;try{X=1,Mc(e,t,n,r)}finally{X=i,vr.transition=s}}function ay(e,t,n,r){var i=X,s=vr.transition;vr.transition=null;try{X=4,Mc(e,t,n,r)}finally{X=i,vr.transition=s}}function Mc(e,t,n,r){if(fa){var i=Cl(e,t,n,r);if(i===null)Do(e,t,r,pa,n),Xu(e,r);else if(ry(i,e,t,n,r))r.stopPropagation();else if(Xu(e,r),t&4&&-1<ny.indexOf(e)){for(;i!==null;){var s=rs(i);if(s!==null&&op(s),s=Cl(e,t,n,r),s===null&&Do(e,t,r,pa,n),s===i)break;i=s}i!==null&&r.stopPropagation()}else Do(e,t,r,null,n)}}var pa=null;function Cl(e,t,n,r){if(pa=null,e=jc(r),e=Pn(e),e!==null)if(t=Gn(e),t===null)e=null;else if(n=t.tag,n===13){if(e=Jf(t),e!==null)return e;e=null}else if(n===3){if(t.stateNode.current.memoizedState.isDehydrated)return t.tag===3?t.stateNode.containerInfo:null;e=null}else t!==e&&(e=null);return pa=e,null}function hp(e){switch(e){case"cancel":case"click":case"close":case"contextmenu":case"copy":case"cut":case"auxclick":case"dblclick":case"dragend":case"dragstart":case"drop":case"focusin":case"focusout":case"input":case"invalid":case"keydown":case"keypress":case"keyup":case"mousedown":case"mouseup":case"paste":case"pause":case"play":case"pointercancel":case"pointerdown":case"pointerup":case"ratechange":case"reset":case"resize":case"seeked":case"submit":case"touchcancel":case"touchend":case"touchstart":case"volumechange":case"change":case"selectionchange":case"textInput":case"compositionstart":case"compositionend":case"compositionupdate":case"beforeblur":case"afterblur":case"beforeinput":case"blur":case"fullscreenchange":case"focus":case"hashchange":case"popstate":case"select":case"selectstart":return 1;case"drag":case"dragenter":case"dragexit":case"dragleave":case"dragover":case"mousemove":case"mouseout":case"mouseover":case"pointermove":case"pointerout":case"pointerover":case"scroll":case"toggle":case"touchmove":case"wheel":case"mouseenter":case"mouseleave":case"pointerenter":case"pointerleave":return 4;case"message":switch(Xv()){case Sc:return 1;case rp:return 4;case da:case Kv:return 16;case ip:return 536870912;default:return 16}default:return 16}}var Zt=null,Pc=null,Xs=null;function fp(){if(Xs)return Xs;var e,t=Pc,n=t.length,r,i="value"in Zt?Zt.value:Zt.textContent,s=i.length;for(e=0;e<n&&t[e]===i[e];e++);var a=n-e;for(r=1;r<=a&&t[n-r]===i[s-r];r++);return Xs=i.slice(e,1<r?1-r:void 0)}function Ks(e){var t=e.keyCode;return"charCode"in e?(e=e.charCode,e===0&&t===13&&(e=13)):e=t,e===10&&(e=13),32<=e||e===13?e:0}function ks(){return!0}function Qu(){return!1}function et(e){function t(n,r,i,s,a){this._reactName=n,this._targetInst=i,this.type=r,this.nativeEvent=s,this.target=a,this.currentTarget=null;for(var o in e)e.hasOwnProperty(o)&&(n=e[o],this[o]=n?n(s):s[o]);return this.isDefaultPrevented=(s.defaultPrevented!=null?s.defaultPrevented:s.returnValue===!1)?ks:Qu,this.isPropagationStopped=Qu,this}return ae(t.prototype,{preventDefault:function(){this.defaultPrevented=!0;var n=this.nativeEvent;n&&(n.preventDefault?n.preventDefault():typeof n.returnValue!="unknown"&&(n.returnValue=!1),this.isDefaultPrevented=ks)},stopPropagation:function(){var n=this.nativeEvent;n&&(n.stopPropagation?n.stopPropagation():typeof n.cancelBubble!="unknown"&&(n.cancelBubble=!0),this.isPropagationStopped=ks)},persist:function(){},isPersistent:ks}),t}var Or={eventPhase:0,bubbles:0,cancelable:0,timeStamp:function(e){return e.timeStamp||Date.now()},defaultPrevented:0,isTrusted:0},Ec=et(Or),ns=ae({},Or,{view:0,detail:0}),oy=et(ns),jo,So,Kr,Ka=ae({},ns,{screenX:0,screenY:0,clientX:0,clientY:0,pageX:0,pageY:0,ctrlKey:0,shiftKey:0,altKey:0,metaKey:0,getModifierState:Tc,button:0,buttons:0,relatedTarget:function(e){return e.relatedTarget===void 0?e.fromElement===e.srcElement?e.toElement:e.fromElement:e.relatedTarget},movementX:function(e){return"movementX"in e?e.movementX:(e!==Kr&&(Kr&&e.type==="mousemove"?(jo=e.screenX-Kr.screenX,So=e.screenY-Kr.screenY):So=jo=0,Kr=e),jo)},movementY:function(e){return"movementY"in e?e.movementY:So}}),Gu=et(Ka),ly=ae({},Ka,{dataTransfer:0}),cy=et(ly),uy=ae({},ns,{relatedTarget:0}),No=et(uy),dy=ae({},Or,{animationName:0,elapsedTime:0,pseudoElement:0}),hy=et(dy),fy=ae({},Or,{clipboardData:function(e){return"clipboardData"in e?e.clipboardData:window.clipboardData}}),py=et(fy),my=ae({},Or,{data:0}),Zu=et(my),gy={Esc:"Escape",Spacebar:" ",Left:"ArrowLeft",Up:"ArrowUp",Right:"ArrowRight",Down:"ArrowDown",Del:"Delete",Win:"OS",Menu:"ContextMenu",Apps:"ContextMenu",Scroll:"ScrollLock",MozPrintableKey:"Unidentified"},vy={8:"Backspace",9:"Tab",12:"Clear",13:"Enter",16:"Shift",17:"Control",18:"Alt",19:"Pause",20:"CapsLock",27:"Escape",32:" ",33:"PageUp",34:"PageDown",35:"End",36:"Home",37:"ArrowLeft",38:"ArrowUp",39:"ArrowRight",40:"ArrowDown",45:"Insert",46:"Delete",112:"F1",113:"F2",114:"F3",115:"F4",116:"F5",117:"F6",118:"F7",119:"F8",120:"F9",121:"F10",122:"F11",123:"F12",144:"NumLock",145:"ScrollLock",224:"Meta"},yy={Alt:"altKey",Control:"ctrlKey",Meta:"metaKey",Shift:"shiftKey"};function xy(e){var t=this.nativeEvent;return t.getModifierState?t.getModifierState(e):(e=yy[e])?!!t[e]:!1}function Tc(){return xy}var by=ae({},ns,{key:function(e){if(e.key){var t=gy[e.key]||e.key;if(t!=="Unidentified")return t}return e.type==="keypress"?(e=Ks(e),e===13?"Enter":String.fromCharCode(e)):e.type==="keydown"||e.type==="keyup"?vy[e.keyCode]||"Unidentified":""},code:0,location:0,ctrlKey:0,shiftKey:0,altKey:0,metaKey:0,repeat:0,locale:0,getModifierState:Tc,charCode:function(e){return e.type==="keypress"?Ks(e):0},keyCode:function(e){return e.type==="keydown"||e.type==="keyup"?e.keyCode:0},which:function(e){return e.type==="keypress"?Ks(e):e.type==="keydown"||e.type==="keyup"?e.keyCode:0}}),ky=et(by),wy=ae({},Ka,{pointerId:0,width:0,height:0,pressure:0,tangentialPressure:0,tiltX:0,tiltY:0,twist:0,pointerType:0,isPrimary:0}),qu=et(wy),_y=ae({},ns,{touches:0,targetTouches:0,changedTouches:0,altKey:0,metaKey:0,ctrlKey:0,shiftKey:0,getModifierState:Tc}),jy=et(_y),Sy=ae({},Or,{propertyName:0,elapsedTime:0,pseudoElement:0}),Ny=et(Sy),Cy=ae({},Ka,{deltaX:function(e){return"deltaX"in e?e.deltaX:"wheelDeltaX"in e?-e.wheelDeltaX:0},deltaY:function(e){return"deltaY"in e?e.deltaY:"wheelDeltaY"in e?-e.wheelDeltaY:"wheelDelta"in e?-e.wheelDelta:0},deltaZ:0,deltaMode:0}),My=et(Cy),Py=[9,13,27,32],zc=Ft&&"CompositionEvent"in window,pi=null;Ft&&"documentMode"in document&&(pi=document.documentMode);var Ey=Ft&&"TextEvent"in window&&!pi,pp=Ft&&(!zc||pi&&8<pi&&11>=pi),Ju=" ",ed=!1;function mp(e,t){switch(e){case"keyup":return Py.indexOf(t.keyCode)!==-1;case"keydown":return t.keyCode!==229;case"keypress":case"mousedown":case"focusout":return!0;default:return!1}}function gp(e){return e=e.detail,typeof e=="object"&&"data"in e?e.data:null}var ir=!1;function Ty(e,t){switch(e){case"compositionend":return gp(t);case"keypress":return t.which!==32?null:(ed=!0,Ju);case"textInput":return e=t.data,e===Ju&&ed?null:e;default:return null}}function zy(e,t){if(ir)return e==="compositionend"||!zc&&mp(e,t)?(e=fp(),Xs=Pc=Zt=null,ir=!1,e):null;switch(e){case"paste":return null;case"keypress":if(!(t.ctrlKey||t.altKey||t.metaKey)||t.ctrlKey&&t.altKey){if(t.char&&1<t.char.length)return t.char;if(t.which)return String.fromCharCode(t.which)}return null;case"compositionend":return pp&&t.locale!=="ko"?null:t.data;default:return null}}var Dy={color:!0,date:!0,datetime:!0,"datetime-local":!0,email:!0,month:!0,number:!0,password:!0,range:!0,search:!0,tel:!0,text:!0,time:!0,url:!0,week:!0};function td(e){var t=e&&e.nodeName&&e.nodeName.toLowerCase();return t==="input"?!!Dy[e.type]:t==="textarea"}function vp(e,t,n,r){Kf(r),t=ma(t,"onChange"),0<t.length&&(n=new Ec("onChange","change",null,n,r),e.push({event:n,listeners:t}))}var mi=null,zi=null;function Ry(e){Mp(e,0)}function Qa(e){var t=or(e);if($f(t))return e}function Ly(e,t){if(e==="change")return t}var yp=!1;if(Ft){var Co;if(Ft){var Mo="oninput"in document;if(!Mo){var nd=document.createElement("div");nd.setAttribute("oninput","return;"),Mo=typeof nd.oninput=="function"}Co=Mo}else Co=!1;yp=Co&&(!document.documentMode||9<document.documentMode)}function rd(){mi&&(mi.detachEvent("onpropertychange",xp),zi=mi=null)}function xp(e){if(e.propertyName==="value"&&Qa(zi)){var t=[];vp(t,zi,e,jc(e)),qf(Ry,t)}}function Oy(e,t,n){e==="focusin"?(rd(),mi=t,zi=n,mi.attachEvent("onpropertychange",xp)):e==="focusout"&&rd()}function Ay(e){if(e==="selectionchange"||e==="keyup"||e==="keydown")return Qa(zi)}function Iy(e,t){if(e==="click")return Qa(t)}function Fy(e,t){if(e==="input"||e==="change")return Qa(t)}function By(e,t){return e===t&&(e!==0||1/e===1/t)||e!==e&&t!==t}var gt=typeof Object.is=="function"?Object.is:By;function Di(e,t){if(gt(e,t))return!0;if(typeof e!="object"||e===null||typeof t!="object"||t===null)return!1;var n=Object.keys(e),r=Object.keys(t);if(n.length!==r.length)return!1;for(r=0;r<n.length;r++){var i=n[r];if(!cl.call(t,i)||!gt(e[i],t[i]))return!1}return!0}function id(e){for(;e&&e.firstChild;)e=e.firstChild;return e}function sd(e,t){var n=id(e);e=0;for(var r;n;){if(n.nodeType===3){if(r=e+n.textContent.length,e<=t&&r>=t)return{node:n,offset:t-e};e=r}e:{for(;n;){if(n.nextSibling){n=n.nextSibling;break e}n=n.parentNode}n=void 0}n=id(n)}}function bp(e,t){return e&&t?e===t?!0:e&&e.nodeType===3?!1:t&&t.nodeType===3?bp(e,t.parentNode):"contains"in e?e.contains(t):e.compareDocumentPosition?!!(e.compareDocumentPosition(t)&16):!1:!1}function kp(){for(var e=window,t=la();t instanceof e.HTMLIFrameElement;){try{var n=typeof t.contentWindow.location.href=="string"}catch{n=!1}if(n)e=t.contentWindow;else break;t=la(e.document)}return t}function Dc(e){var t=e&&e.nodeName&&e.nodeName.toLowerCase();return t&&(t==="input"&&(e.type==="text"||e.type==="search"||e.type==="tel"||e.type==="url"||e.type==="password")||t==="textarea"||e.contentEditable==="true")}function $y(e){var t=kp(),n=e.focusedElem,r=e.selectionRange;if(t!==n&&n&&n.ownerDocument&&bp(n.ownerDocument.documentElement,n)){if(r!==null&&Dc(n)){if(t=r.start,e=r.end,e===void 0&&(e=t),"selectionStart"in n)n.selectionStart=t,n.selectionEnd=Math.min(e,n.value.length);else if(e=(t=n.ownerDocument||document)&&t.defaultView||window,e.getSelection){e=e.getSelection();var i=n.textContent.length,s=Math.min(r.start,i);r=r.end===void 0?s:Math.min(r.end,i),!e.extend&&s>r&&(i=r,r=s,s=i),i=sd(n,s);var a=sd(n,r);i&&a&&(e.rangeCount!==1||e.anchorNode!==i.node||e.anchorOffset!==i.offset||e.focusNode!==a.node||e.focusOffset!==a.offset)&&(t=t.createRange(),t.setStart(i.node,i.offset),e.removeAllRanges(),s>r?(e.addRange(t),e.extend(a.node,a.offset)):(t.setEnd(a.node,a.offset),e.addRange(t)))}}for(t=[],e=n;e=e.parentNode;)e.nodeType===1&&t.push({element:e,left:e.scrollLeft,top:e.scrollTop});for(typeof n.focus=="function"&&n.focus(),n=0;n<t.length;n++)e=t[n],e.element.scrollLeft=e.left,e.element.scrollTop=e.top}}var Hy=Ft&&"documentMode"in document&&11>=document.documentMode,sr=null,Ml=null,gi=null,Pl=!1;function ad(e,t,n){var r=n.window===n?n.document:n.nodeType===9?n:n.ownerDocument;Pl||sr==null||sr!==la(r)||(r=sr,"selectionStart"in r&&Dc(r)?r={start:r.selectionStart,end:r.selectionEnd}:(r=(r.ownerDocument&&r.ownerDocument.defaultView||window).getSelection(),r={anchorNode:r.anchorNode,anchorOffset:r.anchorOffset,focusNode:r.focusNode,focusOffset:r.focusOffset}),gi&&Di(gi,r)||(gi=r,r=ma(Ml,"onSelect"),0<r.length&&(t=new Ec("onSelect","select",null,t,n),e.push({event:t,listeners:r}),t.target=sr)))}function ws(e,t){var n={};return n[e.toLowerCase()]=t.toLowerCase(),n["Webkit"+e]="webkit"+t,n["Moz"+e]="moz"+t,n}var ar={animationend:ws("Animation","AnimationEnd"),animationiteration:ws("Animation","AnimationIteration"),animationstart:ws("Animation","AnimationStart"),transitionend:ws("Transition","TransitionEnd")},Po={},wp={};Ft&&(wp=document.createElement("div").style,"AnimationEvent"in window||(delete ar.animationend.animation,delete ar.animationiteration.animation,delete ar.animationstart.animation),"TransitionEvent"in window||delete ar.transitionend.transition);function Ga(e){if(Po[e])return Po[e];if(!ar[e])return e;var t=ar[e],n;for(n in t)if(t.hasOwnProperty(n)&&n in wp)return Po[e]=t[n];return e}var _p=Ga("animationend"),jp=Ga("animationiteration"),Sp=Ga("animationstart"),Np=Ga("transitionend"),Cp=new Map,od="abort auxClick cancel canPlay canPlayThrough click close contextMenu copy cut drag dragEnd dragEnter dragExit dragLeave dragOver dragStart drop durationChange emptied encrypted ended error gotPointerCapture input invalid keyDown keyPress keyUp load loadedData loadedMetadata loadStart lostPointerCapture mouseDown mouseMove mouseOut mouseOver mouseUp paste pause play playing pointerCancel pointerDown pointerMove pointerOut pointerOver pointerUp progress rateChange reset resize seeked seeking stalled submit suspend timeUpdate touchCancel touchEnd touchStart volumeChange scroll toggle touchMove waiting wheel".split(" ");function yn(e,t){Cp.set(e,t),Qn(t,[e])}for(var Eo=0;Eo<od.length;Eo++){var To=od[Eo],Wy=To.toLowerCase(),Vy=To[0].toUpperCase()+To.slice(1);yn(Wy,"on"+Vy)}yn(_p,"onAnimationEnd");yn(jp,"onAnimationIteration");yn(Sp,"onAnimationStart");yn("dblclick","onDoubleClick");yn("focusin","onFocus");yn("focusout","onBlur");yn(Np,"onTransitionEnd");jr("onMouseEnter",["mouseout","mouseover"]);jr("onMouseLeave",["mouseout","mouseover"]);jr("onPointerEnter",["pointerout","pointerover"]);jr("onPointerLeave",["pointerout","pointerover"]);Qn("onChange","change click focusin focusout input keydown keyup selectionchange".split(" "));Qn("onSelect","focusout contextmenu dragend focusin keydown keyup mousedown mouseup selectionchange".split(" "));Qn("onBeforeInput",["compositionend","keypress","textInput","paste"]);Qn("onCompositionEnd","compositionend focusout keydown keypress keyup mousedown".split(" "));Qn("onCompositionStart","compositionstart focusout keydown keypress keyup mousedown".split(" "));Qn("onCompositionUpdate","compositionupdate focusout keydown keypress keyup mousedown".split(" "));var ai="abort canplay canplaythrough durationchange emptied encrypted ended error loadeddata loadedmetadata loadstart pause play playing progress ratechange resize seeked seeking stalled suspend timeupdate volumechange waiting".split(" "),Uy=new Set("cancel close invalid load scroll toggle".split(" ").concat(ai));function ld(e,t,n){var r=e.type||"unknown-event";e.currentTarget=n,Wv(r,t,void 0,e),e.currentTarget=null}function Mp(e,t){t=(t&4)!==0;for(var n=0;n<e.length;n++){var r=e[n],i=r.event;r=r.listeners;e:{var s=void 0;if(t)for(var a=r.length-1;0<=a;a--){var o=r[a],l=o.instance,u=o.currentTarget;if(o=o.listener,l!==s&&i.isPropagationStopped())break e;ld(i,o,u),s=l}else for(a=0;a<r.length;a++){if(o=r[a],l=o.instance,u=o.currentTarget,o=o.listener,l!==s&&i.isPropagationStopped())break e;ld(i,o,u),s=l}}}if(ua)throw e=jl,ua=!1,jl=null,e}function ee(e,t){var n=t[Rl];n===void 0&&(n=t[Rl]=new Set);var r=e+"__bubble";n.has(r)||(Pp(t,e,2,!1),n.add(r))}function zo(e,t,n){var r=0;t&&(r|=4),Pp(n,e,r,t)}var _s="_reactListening"+Math.random().toString(36).slice(2);function Ri(e){if(!e[_s]){e[_s]=!0,Of.forEach(function(n){n!=="selectionchange"&&(Uy.has(n)||zo(n,!1,e),zo(n,!0,e))});var t=e.nodeType===9?e:e.ownerDocument;t===null||t[_s]||(t[_s]=!0,zo("selectionchange",!1,t))}}function Pp(e,t,n,r){switch(hp(t)){case 1:var i=sy;break;case 4:i=ay;break;default:i=Mc}n=i.bind(null,t,n,e),i=void 0,!_l||t!=="touchstart"&&t!=="touchmove"&&t!=="wheel"||(i=!0),r?i!==void 0?e.addEventListener(t,n,{capture:!0,passive:i}):e.addEventListener(t,n,!0):i!==void 0?e.addEventListener(t,n,{passive:i}):e.addEventListener(t,n,!1)}function Do(e,t,n,r,i){var s=r;if(!(t&1)&&!(t&2)&&r!==null)e:for(;;){if(r===null)return;var a=r.tag;if(a===3||a===4){var o=r.stateNode.containerInfo;if(o===i||o.nodeType===8&&o.parentNode===i)break;if(a===4)for(a=r.return;a!==null;){var l=a.tag;if((l===3||l===4)&&(l=a.stateNode.containerInfo,l===i||l.nodeType===8&&l.parentNode===i))return;a=a.return}for(;o!==null;){if(a=Pn(o),a===null)return;if(l=a.tag,l===5||l===6){r=s=a;continue e}o=o.parentNode}}r=r.return}qf(function(){var u=s,d=jc(n),h=[];e:{var f=Cp.get(e);if(f!==void 0){var p=Ec,m=e;switch(e){case"keypress":if(Ks(n)===0)break e;case"keydown":case"keyup":p=ky;break;case"focusin":m="focus",p=No;break;case"focusout":m="blur",p=No;break;case"beforeblur":case"afterblur":p=No;break;case"click":if(n.button===2)break e;case"auxclick":case"dblclick":case"mousedown":case"mousemove":case"mouseup":case"mouseout":case"mouseover":case"contextmenu":p=Gu;break;case"drag":case"dragend":case"dragenter":case"dragexit":case"dragleave":case"dragover":case"dragstart":case"drop":p=cy;break;case"touchcancel":case"touchend":case"touchmove":case"touchstart":p=jy;break;case _p:case jp:case Sp:p=hy;break;case Np:p=Ny;break;case"scroll":p=oy;break;case"wheel":p=My;break;case"copy":case"cut":case"paste":p=py;break;case"gotpointercapture":case"lostpointercapture":case"pointercancel":case"pointerdown":case"pointermove":case"pointerout":case"pointerover":case"pointerup":p=qu}var v=(t&4)!==0,y=!v&&e==="scroll",g=v?f!==null?f+"Capture":null:f;v=[];for(var x=u,b;x!==null;){b=x;var k=b.stateNode;if(b.tag===5&&k!==null&&(b=k,g!==null&&(k=Mi(x,g),k!=null&&v.push(Li(x,k,b)))),y)break;x=x.return}0<v.length&&(f=new p(f,m,null,n,d),h.push({event:f,listeners:v}))}}if(!(t&7)){e:{if(f=e==="mouseover"||e==="pointerover",p=e==="mouseout"||e==="pointerout",f&&n!==kl&&(m=n.relatedTarget||n.fromElement)&&(Pn(m)||m[Bt]))break e;if((p||f)&&(f=d.window===d?d:(f=d.ownerDocument)?f.defaultView||f.parentWindow:window,p?(m=n.relatedTarget||n.toElement,p=u,m=m?Pn(m):null,m!==null&&(y=Gn(m),m!==y||m.tag!==5&&m.tag!==6)&&(m=null)):(p=null,m=u),p!==m)){if(v=Gu,k="onMouseLeave",g="onMouseEnter",x="mouse",(e==="pointerout"||e==="pointerover")&&(v=qu,k="onPointerLeave",g="onPointerEnter",x="pointer"),y=p==null?f:or(p),b=m==null?f:or(m),f=new v(k,x+"leave",p,n,d),f.target=y,f.relatedTarget=b,k=null,Pn(d)===u&&(v=new v(g,x+"enter",m,n,d),v.target=b,v.relatedTarget=y,k=v),y=k,p&&m)t:{for(v=p,g=m,x=0,b=v;b;b=Jn(b))x++;for(b=0,k=g;k;k=Jn(k))b++;for(;0<x-b;)v=Jn(v),x--;for(;0<b-x;)g=Jn(g),b--;for(;x--;){if(v===g||g!==null&&v===g.alternate)break t;v=Jn(v),g=Jn(g)}v=null}else v=null;p!==null&&cd(h,f,p,v,!1),m!==null&&y!==null&&cd(h,y,m,v,!0)}}e:{if(f=u?or(u):window,p=f.nodeName&&f.nodeName.toLowerCase(),p==="select"||p==="input"&&f.type==="file")var w=Ly;else if(td(f))if(yp)w=Fy;else{w=Ay;var j=Oy}else(p=f.nodeName)&&p.toLowerCase()==="input"&&(f.type==="checkbox"||f.type==="radio")&&(w=Iy);if(w&&(w=w(e,u))){vp(h,w,n,d);break e}j&&j(e,f,u),e==="focusout"&&(j=f._wrapperState)&&j.controlled&&f.type==="number"&&gl(f,"number",f.value)}switch(j=u?or(u):window,e){case"focusin":(td(j)||j.contentEditable==="true")&&(sr=j,Ml=u,gi=null);break;case"focusout":gi=Ml=sr=null;break;case"mousedown":Pl=!0;break;case"contextmenu":case"mouseup":case"dragend":Pl=!1,ad(h,n,d);break;case"selectionchange":if(Hy)break;case"keydown":case"keyup":ad(h,n,d)}var S;if(zc)e:{switch(e){case"compositionstart":var N="onCompositionStart";break e;case"compositionend":N="onCompositionEnd";break e;case"compositionupdate":N="onCompositionUpdate";break e}N=void 0}else ir?mp(e,n)&&(N="onCompositionEnd"):e==="keydown"&&n.keyCode===229&&(N="onCompositionStart");N&&(pp&&n.locale!=="ko"&&(ir||N!=="onCompositionStart"?N==="onCompositionEnd"&&ir&&(S=fp()):(Zt=d,Pc="value"in Zt?Zt.value:Zt.textContent,ir=!0)),j=ma(u,N),0<j.length&&(N=new Zu(N,e,null,n,d),h.push({event:N,listeners:j}),S?N.data=S:(S=gp(n),S!==null&&(N.data=S)))),(S=Ey?Ty(e,n):zy(e,n))&&(u=ma(u,"onBeforeInput"),0<u.length&&(d=new Zu("onBeforeInput","beforeinput",null,n,d),h.push({event:d,listeners:u}),d.data=S))}Mp(h,t)})}function Li(e,t,n){return{instance:e,listener:t,currentTarget:n}}function ma(e,t){for(var n=t+"Capture",r=[];e!==null;){var i=e,s=i.stateNode;i.tag===5&&s!==null&&(i=s,s=Mi(e,n),s!=null&&r.unshift(Li(e,s,i)),s=Mi(e,t),s!=null&&r.push(Li(e,s,i))),e=e.return}return r}function Jn(e){if(e===null)return null;do e=e.return;while(e&&e.tag!==5);return e||null}function cd(e,t,n,r,i){for(var s=t._reactName,a=[];n!==null&&n!==r;){var o=n,l=o.alternate,u=o.stateNode;if(l!==null&&l===r)break;o.tag===5&&u!==null&&(o=u,i?(l=Mi(n,s),l!=null&&a.unshift(Li(n,l,o))):i||(l=Mi(n,s),l!=null&&a.push(Li(n,l,o)))),n=n.return}a.length!==0&&e.push({event:t,listeners:a})}var Yy=/\r\n?/g,Xy=/\u0000|\uFFFD/g;function ud(e){return(typeof e=="string"?e:""+e).replace(Yy,`
`).replace(Xy,"")}function js(e,t,n){if(t=ud(t),ud(e)!==t&&n)throw Error(M(425))}function ga(){}var El=null,Tl=null;function zl(e,t){return e==="textarea"||e==="noscript"||typeof t.children=="string"||typeof t.children=="number"||typeof t.dangerouslySetInnerHTML=="object"&&t.dangerouslySetInnerHTML!==null&&t.dangerouslySetInnerHTML.__html!=null}var Dl=typeof setTimeout=="function"?setTimeout:void 0,Ky=typeof clearTimeout=="function"?clearTimeout:void 0,dd=typeof Promise=="function"?Promise:void 0,Qy=typeof queueMicrotask=="function"?queueMicrotask:typeof dd<"u"?function(e){return dd.resolve(null).then(e).catch(Gy)}:Dl;function Gy(e){setTimeout(function(){throw e})}function Ro(e,t){var n=t,r=0;do{var i=n.nextSibling;if(e.removeChild(n),i&&i.nodeType===8)if(n=i.data,n==="/$"){if(r===0){e.removeChild(i),Ti(t);return}r--}else n!=="$"&&n!=="$?"&&n!=="$!"||r++;n=i}while(n);Ti(t)}function ln(e){for(;e!=null;e=e.nextSibling){var t=e.nodeType;if(t===1||t===3)break;if(t===8){if(t=e.data,t==="$"||t==="$!"||t==="$?")break;if(t==="/$")return null}}return e}function hd(e){e=e.previousSibling;for(var t=0;e;){if(e.nodeType===8){var n=e.data;if(n==="$"||n==="$!"||n==="$?"){if(t===0)return e;t--}else n==="/$"&&t++}e=e.previousSibling}return null}var Ar=Math.random().toString(36).slice(2),jt="__reactFiber$"+Ar,Oi="__reactProps$"+Ar,Bt="__reactContainer$"+Ar,Rl="__reactEvents$"+Ar,Zy="__reactListeners$"+Ar,qy="__reactHandles$"+Ar;function Pn(e){var t=e[jt];if(t)return t;for(var n=e.parentNode;n;){if(t=n[Bt]||n[jt]){if(n=t.alternate,t.child!==null||n!==null&&n.child!==null)for(e=hd(e);e!==null;){if(n=e[jt])return n;e=hd(e)}return t}e=n,n=e.parentNode}return null}function rs(e){return e=e[jt]||e[Bt],!e||e.tag!==5&&e.tag!==6&&e.tag!==13&&e.tag!==3?null:e}function or(e){if(e.tag===5||e.tag===6)return e.stateNode;throw Error(M(33))}function Za(e){return e[Oi]||null}var Ll=[],lr=-1;function xn(e){return{current:e}}function ne(e){0>lr||(e.current=Ll[lr],Ll[lr]=null,lr--)}function G(e,t){lr++,Ll[lr]=e.current,e.current=t}var mn={},ze=xn(mn),Ue=xn(!1),Hn=mn;function Sr(e,t){var n=e.type.contextTypes;if(!n)return mn;var r=e.stateNode;if(r&&r.__reactInternalMemoizedUnmaskedChildContext===t)return r.__reactInternalMemoizedMaskedChildContext;var i={},s;for(s in n)i[s]=t[s];return r&&(e=e.stateNode,e.__reactInternalMemoizedUnmaskedChildContext=t,e.__reactInternalMemoizedMaskedChildContext=i),i}function Ye(e){return e=e.childContextTypes,e!=null}function va(){ne(Ue),ne(ze)}function fd(e,t,n){if(ze.current!==mn)throw Error(M(168));G(ze,t),G(Ue,n)}function Ep(e,t,n){var r=e.stateNode;if(t=t.childContextTypes,typeof r.getChildContext!="function")return n;r=r.getChildContext();for(var i in r)if(!(i in t))throw Error(M(108,Ov(e)||"Unknown",i));return ae({},n,r)}function ya(e){return e=(e=e.stateNode)&&e.__reactInternalMemoizedMergedChildContext||mn,Hn=ze.current,G(ze,e),G(Ue,Ue.current),!0}function pd(e,t,n){var r=e.stateNode;if(!r)throw Error(M(169));n?(e=Ep(e,t,Hn),r.__reactInternalMemoizedMergedChildContext=e,ne(Ue),ne(ze),G(ze,e)):ne(Ue),G(Ue,n)}var Dt=null,qa=!1,Lo=!1;function Tp(e){Dt===null?Dt=[e]:Dt.push(e)}function Jy(e){qa=!0,Tp(e)}function bn(){if(!Lo&&Dt!==null){Lo=!0;var e=0,t=X;try{var n=Dt;for(X=1;e<n.length;e++){var r=n[e];do r=r(!0);while(r!==null)}Dt=null,qa=!1}catch(i){throw Dt!==null&&(Dt=Dt.slice(e+1)),np(Sc,bn),i}finally{X=t,Lo=!1}}return null}var cr=[],ur=0,xa=null,ba=0,nt=[],rt=0,Wn=null,Lt=1,Ot="";function Sn(e,t){cr[ur++]=ba,cr[ur++]=xa,xa=e,ba=t}function zp(e,t,n){nt[rt++]=Lt,nt[rt++]=Ot,nt[rt++]=Wn,Wn=e;var r=Lt;e=Ot;var i=32-pt(r)-1;r&=~(1<<i),n+=1;var s=32-pt(t)+i;if(30<s){var a=i-i%5;s=(r&(1<<a)-1).toString(32),r>>=a,i-=a,Lt=1<<32-pt(t)+i|n<<i|r,Ot=s+e}else Lt=1<<s|n<<i|r,Ot=e}function Rc(e){e.return!==null&&(Sn(e,1),zp(e,1,0))}function Lc(e){for(;e===xa;)xa=cr[--ur],cr[ur]=null,ba=cr[--ur],cr[ur]=null;for(;e===Wn;)Wn=nt[--rt],nt[rt]=null,Ot=nt[--rt],nt[rt]=null,Lt=nt[--rt],nt[rt]=null}var Ze=null,Ge=null,re=!1,ft=null;function Dp(e,t){var n=it(5,null,null,0);n.elementType="DELETED",n.stateNode=t,n.return=e,t=e.deletions,t===null?(e.deletions=[n],e.flags|=16):t.push(n)}function md(e,t){switch(e.tag){case 5:var n=e.type;return t=t.nodeType!==1||n.toLowerCase()!==t.nodeName.toLowerCase()?null:t,t!==null?(e.stateNode=t,Ze=e,Ge=ln(t.firstChild),!0):!1;case 6:return t=e.pendingProps===""||t.nodeType!==3?null:t,t!==null?(e.stateNode=t,Ze=e,Ge=null,!0):!1;case 13:return t=t.nodeType!==8?null:t,t!==null?(n=Wn!==null?{id:Lt,overflow:Ot}:null,e.memoizedState={dehydrated:t,treeContext:n,retryLane:1073741824},n=it(18,null,null,0),n.stateNode=t,n.return=e,e.child=n,Ze=e,Ge=null,!0):!1;default:return!1}}function Ol(e){return(e.mode&1)!==0&&(e.flags&128)===0}function Al(e){if(re){var t=Ge;if(t){var n=t;if(!md(e,t)){if(Ol(e))throw Error(M(418));t=ln(n.nextSibling);var r=Ze;t&&md(e,t)?Dp(r,n):(e.flags=e.flags&-4097|2,re=!1,Ze=e)}}else{if(Ol(e))throw Error(M(418));e.flags=e.flags&-4097|2,re=!1,Ze=e}}}function gd(e){for(e=e.return;e!==null&&e.tag!==5&&e.tag!==3&&e.tag!==13;)e=e.return;Ze=e}function Ss(e){if(e!==Ze)return!1;if(!re)return gd(e),re=!0,!1;var t;if((t=e.tag!==3)&&!(t=e.tag!==5)&&(t=e.type,t=t!=="head"&&t!=="body"&&!zl(e.type,e.memoizedProps)),t&&(t=Ge)){if(Ol(e))throw Rp(),Error(M(418));for(;t;)Dp(e,t),t=ln(t.nextSibling)}if(gd(e),e.tag===13){if(e=e.memoizedState,e=e!==null?e.dehydrated:null,!e)throw Error(M(317));e:{for(e=e.nextSibling,t=0;e;){if(e.nodeType===8){var n=e.data;if(n==="/$"){if(t===0){Ge=ln(e.nextSibling);break e}t--}else n!=="$"&&n!=="$!"&&n!=="$?"||t++}e=e.nextSibling}Ge=null}}else Ge=Ze?ln(e.stateNode.nextSibling):null;return!0}function Rp(){for(var e=Ge;e;)e=ln(e.nextSibling)}function Nr(){Ge=Ze=null,re=!1}function Oc(e){ft===null?ft=[e]:ft.push(e)}var ex=Wt.ReactCurrentBatchConfig;function Qr(e,t,n){if(e=n.ref,e!==null&&typeof e!="function"&&typeof e!="object"){if(n._owner){if(n=n._owner,n){if(n.tag!==1)throw Error(M(309));var r=n.stateNode}if(!r)throw Error(M(147,e));var i=r,s=""+e;return t!==null&&t.ref!==null&&typeof t.ref=="function"&&t.ref._stringRef===s?t.ref:(t=function(a){var o=i.refs;a===null?delete o[s]:o[s]=a},t._stringRef=s,t)}if(typeof e!="string")throw Error(M(284));if(!n._owner)throw Error(M(290,e))}return e}function Ns(e,t){throw e=Object.prototype.toString.call(t),Error(M(31,e==="[object Object]"?"object with keys {"+Object.keys(t).join(", ")+"}":e))}function vd(e){var t=e._init;return t(e._payload)}function Lp(e){function t(g,x){if(e){var b=g.deletions;b===null?(g.deletions=[x],g.flags|=16):b.push(x)}}function n(g,x){if(!e)return null;for(;x!==null;)t(g,x),x=x.sibling;return null}function r(g,x){for(g=new Map;x!==null;)x.key!==null?g.set(x.key,x):g.set(x.index,x),x=x.sibling;return g}function i(g,x){return g=hn(g,x),g.index=0,g.sibling=null,g}function s(g,x,b){return g.index=b,e?(b=g.alternate,b!==null?(b=b.index,b<x?(g.flags|=2,x):b):(g.flags|=2,x)):(g.flags|=1048576,x)}function a(g){return e&&g.alternate===null&&(g.flags|=2),g}function o(g,x,b,k){return x===null||x.tag!==6?(x=Ho(b,g.mode,k),x.return=g,x):(x=i(x,b),x.return=g,x)}function l(g,x,b,k){var w=b.type;return w===rr?d(g,x,b.props.children,k,b.key):x!==null&&(x.elementType===w||typeof w=="object"&&w!==null&&w.$$typeof===Xt&&vd(w)===x.type)?(k=i(x,b.props),k.ref=Qr(g,x,b),k.return=g,k):(k=ta(b.type,b.key,b.props,null,g.mode,k),k.ref=Qr(g,x,b),k.return=g,k)}function u(g,x,b,k){return x===null||x.tag!==4||x.stateNode.containerInfo!==b.containerInfo||x.stateNode.implementation!==b.implementation?(x=Wo(b,g.mode,k),x.return=g,x):(x=i(x,b.children||[]),x.return=g,x)}function d(g,x,b,k,w){return x===null||x.tag!==7?(x=On(b,g.mode,k,w),x.return=g,x):(x=i(x,b),x.return=g,x)}function h(g,x,b){if(typeof x=="string"&&x!==""||typeof x=="number")return x=Ho(""+x,g.mode,b),x.return=g,x;if(typeof x=="object"&&x!==null){switch(x.$$typeof){case ms:return b=ta(x.type,x.key,x.props,null,g.mode,b),b.ref=Qr(g,null,x),b.return=g,b;case nr:return x=Wo(x,g.mode,b),x.return=g,x;case Xt:var k=x._init;return h(g,k(x._payload),b)}if(ii(x)||Vr(x))return x=On(x,g.mode,b,null),x.return=g,x;Ns(g,x)}return null}function f(g,x,b,k){var w=x!==null?x.key:null;if(typeof b=="string"&&b!==""||typeof b=="number")return w!==null?null:o(g,x,""+b,k);if(typeof b=="object"&&b!==null){switch(b.$$typeof){case ms:return b.key===w?l(g,x,b,k):null;case nr:return b.key===w?u(g,x,b,k):null;case Xt:return w=b._init,f(g,x,w(b._payload),k)}if(ii(b)||Vr(b))return w!==null?null:d(g,x,b,k,null);Ns(g,b)}return null}function p(g,x,b,k,w){if(typeof k=="string"&&k!==""||typeof k=="number")return g=g.get(b)||null,o(x,g,""+k,w);if(typeof k=="object"&&k!==null){switch(k.$$typeof){case ms:return g=g.get(k.key===null?b:k.key)||null,l(x,g,k,w);case nr:return g=g.get(k.key===null?b:k.key)||null,u(x,g,k,w);case Xt:var j=k._init;return p(g,x,b,j(k._payload),w)}if(ii(k)||Vr(k))return g=g.get(b)||null,d(x,g,k,w,null);Ns(x,k)}return null}function m(g,x,b,k){for(var w=null,j=null,S=x,N=x=0,T=null;S!==null&&N<b.length;N++){S.index>N?(T=S,S=null):T=S.sibling;var E=f(g,S,b[N],k);if(E===null){S===null&&(S=T);break}e&&S&&E.alternate===null&&t(g,S),x=s(E,x,N),j===null?w=E:j.sibling=E,j=E,S=T}if(N===b.length)return n(g,S),re&&Sn(g,N),w;if(S===null){for(;N<b.length;N++)S=h(g,b[N],k),S!==null&&(x=s(S,x,N),j===null?w=S:j.sibling=S,j=S);return re&&Sn(g,N),w}for(S=r(g,S);N<b.length;N++)T=p(S,g,N,b[N],k),T!==null&&(e&&T.alternate!==null&&S.delete(T.key===null?N:T.key),x=s(T,x,N),j===null?w=T:j.sibling=T,j=T);return e&&S.forEach(function(L){return t(g,L)}),re&&Sn(g,N),w}function v(g,x,b,k){var w=Vr(b);if(typeof w!="function")throw Error(M(150));if(b=w.call(b),b==null)throw Error(M(151));for(var j=w=null,S=x,N=x=0,T=null,E=b.next();S!==null&&!E.done;N++,E=b.next()){S.index>N?(T=S,S=null):T=S.sibling;var L=f(g,S,E.value,k);if(L===null){S===null&&(S=T);break}e&&S&&L.alternate===null&&t(g,S),x=s(L,x,N),j===null?w=L:j.sibling=L,j=L,S=T}if(E.done)return n(g,S),re&&Sn(g,N),w;if(S===null){for(;!E.done;N++,E=b.next())E=h(g,E.value,k),E!==null&&(x=s(E,x,N),j===null?w=E:j.sibling=E,j=E);return re&&Sn(g,N),w}for(S=r(g,S);!E.done;N++,E=b.next())E=p(S,g,N,E.value,k),E!==null&&(e&&E.alternate!==null&&S.delete(E.key===null?N:E.key),x=s(E,x,N),j===null?w=E:j.sibling=E,j=E);return e&&S.forEach(function(A){return t(g,A)}),re&&Sn(g,N),w}function y(g,x,b,k){if(typeof b=="object"&&b!==null&&b.type===rr&&b.key===null&&(b=b.props.children),typeof b=="object"&&b!==null){switch(b.$$typeof){case ms:e:{for(var w=b.key,j=x;j!==null;){if(j.key===w){if(w=b.type,w===rr){if(j.tag===7){n(g,j.sibling),x=i(j,b.props.children),x.return=g,g=x;break e}}else if(j.elementType===w||typeof w=="object"&&w!==null&&w.$$typeof===Xt&&vd(w)===j.type){n(g,j.sibling),x=i(j,b.props),x.ref=Qr(g,j,b),x.return=g,g=x;break e}n(g,j);break}else t(g,j);j=j.sibling}b.type===rr?(x=On(b.props.children,g.mode,k,b.key),x.return=g,g=x):(k=ta(b.type,b.key,b.props,null,g.mode,k),k.ref=Qr(g,x,b),k.return=g,g=k)}return a(g);case nr:e:{for(j=b.key;x!==null;){if(x.key===j)if(x.tag===4&&x.stateNode.containerInfo===b.containerInfo&&x.stateNode.implementation===b.implementation){n(g,x.sibling),x=i(x,b.children||[]),x.return=g,g=x;break e}else{n(g,x);break}else t(g,x);x=x.sibling}x=Wo(b,g.mode,k),x.return=g,g=x}return a(g);case Xt:return j=b._init,y(g,x,j(b._payload),k)}if(ii(b))return m(g,x,b,k);if(Vr(b))return v(g,x,b,k);Ns(g,b)}return typeof b=="string"&&b!==""||typeof b=="number"?(b=""+b,x!==null&&x.tag===6?(n(g,x.sibling),x=i(x,b),x.return=g,g=x):(n(g,x),x=Ho(b,g.mode,k),x.return=g,g=x),a(g)):n(g,x)}return y}var Cr=Lp(!0),Op=Lp(!1),ka=xn(null),wa=null,dr=null,Ac=null;function Ic(){Ac=dr=wa=null}function Fc(e){var t=ka.current;ne(ka),e._currentValue=t}function Il(e,t,n){for(;e!==null;){var r=e.alternate;if((e.childLanes&t)!==t?(e.childLanes|=t,r!==null&&(r.childLanes|=t)):r!==null&&(r.childLanes&t)!==t&&(r.childLanes|=t),e===n)break;e=e.return}}function yr(e,t){wa=e,Ac=dr=null,e=e.dependencies,e!==null&&e.firstContext!==null&&(e.lanes&t&&(We=!0),e.firstContext=null)}function ot(e){var t=e._currentValue;if(Ac!==e)if(e={context:e,memoizedValue:t,next:null},dr===null){if(wa===null)throw Error(M(308));dr=e,wa.dependencies={lanes:0,firstContext:e}}else dr=dr.next=e;return t}var En=null;function Bc(e){En===null?En=[e]:En.push(e)}function Ap(e,t,n,r){var i=t.interleaved;return i===null?(n.next=n,Bc(t)):(n.next=i.next,i.next=n),t.interleaved=n,$t(e,r)}function $t(e,t){e.lanes|=t;var n=e.alternate;for(n!==null&&(n.lanes|=t),n=e,e=e.return;e!==null;)e.childLanes|=t,n=e.alternate,n!==null&&(n.childLanes|=t),n=e,e=e.return;return n.tag===3?n.stateNode:null}var Kt=!1;function $c(e){e.updateQueue={baseState:e.memoizedState,firstBaseUpdate:null,lastBaseUpdate:null,shared:{pending:null,interleaved:null,lanes:0},effects:null}}function Ip(e,t){e=e.updateQueue,t.updateQueue===e&&(t.updateQueue={baseState:e.baseState,firstBaseUpdate:e.firstBaseUpdate,lastBaseUpdate:e.lastBaseUpdate,shared:e.shared,effects:e.effects})}function It(e,t){return{eventTime:e,lane:t,tag:0,payload:null,callback:null,next:null}}function cn(e,t,n){var r=e.updateQueue;if(r===null)return null;if(r=r.shared,H&2){var i=r.pending;return i===null?t.next=t:(t.next=i.next,i.next=t),r.pending=t,$t(e,n)}return i=r.interleaved,i===null?(t.next=t,Bc(r)):(t.next=i.next,i.next=t),r.interleaved=t,$t(e,n)}function Qs(e,t,n){if(t=t.updateQueue,t!==null&&(t=t.shared,(n&4194240)!==0)){var r=t.lanes;r&=e.pendingLanes,n|=r,t.lanes=n,Nc(e,n)}}function yd(e,t){var n=e.updateQueue,r=e.alternate;if(r!==null&&(r=r.updateQueue,n===r)){var i=null,s=null;if(n=n.firstBaseUpdate,n!==null){do{var a={eventTime:n.eventTime,lane:n.lane,tag:n.tag,payload:n.payload,callback:n.callback,next:null};s===null?i=s=a:s=s.next=a,n=n.next}while(n!==null);s===null?i=s=t:s=s.next=t}else i=s=t;n={baseState:r.baseState,firstBaseUpdate:i,lastBaseUpdate:s,shared:r.shared,effects:r.effects},e.updateQueue=n;return}e=n.lastBaseUpdate,e===null?n.firstBaseUpdate=t:e.next=t,n.lastBaseUpdate=t}function _a(e,t,n,r){var i=e.updateQueue;Kt=!1;var s=i.firstBaseUpdate,a=i.lastBaseUpdate,o=i.shared.pending;if(o!==null){i.shared.pending=null;var l=o,u=l.next;l.next=null,a===null?s=u:a.next=u,a=l;var d=e.alternate;d!==null&&(d=d.updateQueue,o=d.lastBaseUpdate,o!==a&&(o===null?d.firstBaseUpdate=u:o.next=u,d.lastBaseUpdate=l))}if(s!==null){var h=i.baseState;a=0,d=u=l=null,o=s;do{var f=o.lane,p=o.eventTime;if((r&f)===f){d!==null&&(d=d.next={eventTime:p,lane:0,tag:o.tag,payload:o.payload,callback:o.callback,next:null});e:{var m=e,v=o;switch(f=t,p=n,v.tag){case 1:if(m=v.payload,typeof m=="function"){h=m.call(p,h,f);break e}h=m;break e;case 3:m.flags=m.flags&-65537|128;case 0:if(m=v.payload,f=typeof m=="function"?m.call(p,h,f):m,f==null)break e;h=ae({},h,f);break e;case 2:Kt=!0}}o.callback!==null&&o.lane!==0&&(e.flags|=64,f=i.effects,f===null?i.effects=[o]:f.push(o))}else p={eventTime:p,lane:f,tag:o.tag,payload:o.payload,callback:o.callback,next:null},d===null?(u=d=p,l=h):d=d.next=p,a|=f;if(o=o.next,o===null){if(o=i.shared.pending,o===null)break;f=o,o=f.next,f.next=null,i.lastBaseUpdate=f,i.shared.pending=null}}while(!0);if(d===null&&(l=h),i.baseState=l,i.firstBaseUpdate=u,i.lastBaseUpdate=d,t=i.shared.interleaved,t!==null){i=t;do a|=i.lane,i=i.next;while(i!==t)}else s===null&&(i.shared.lanes=0);Un|=a,e.lanes=a,e.memoizedState=h}}function xd(e,t,n){if(e=t.effects,t.effects=null,e!==null)for(t=0;t<e.length;t++){var r=e[t],i=r.callback;if(i!==null){if(r.callback=null,r=n,typeof i!="function")throw Error(M(191,i));i.call(r)}}}var is={},Nt=xn(is),Ai=xn(is),Ii=xn(is);function Tn(e){if(e===is)throw Error(M(174));return e}function Hc(e,t){switch(G(Ii,t),G(Ai,e),G(Nt,is),e=t.nodeType,e){case 9:case 11:t=(t=t.documentElement)?t.namespaceURI:yl(null,"");break;default:e=e===8?t.parentNode:t,t=e.namespaceURI||null,e=e.tagName,t=yl(t,e)}ne(Nt),G(Nt,t)}function Mr(){ne(Nt),ne(Ai),ne(Ii)}function Fp(e){Tn(Ii.current);var t=Tn(Nt.current),n=yl(t,e.type);t!==n&&(G(Ai,e),G(Nt,n))}function Wc(e){Ai.current===e&&(ne(Nt),ne(Ai))}var ie=xn(0);function ja(e){for(var t=e;t!==null;){if(t.tag===13){var n=t.memoizedState;if(n!==null&&(n=n.dehydrated,n===null||n.data==="$?"||n.data==="$!"))return t}else if(t.tag===19&&t.memoizedProps.revealOrder!==void 0){if(t.flags&128)return t}else if(t.child!==null){t.child.return=t,t=t.child;continue}if(t===e)break;for(;t.sibling===null;){if(t.return===null||t.return===e)return null;t=t.return}t.sibling.return=t.return,t=t.sibling}return null}var Oo=[];function Vc(){for(var e=0;e<Oo.length;e++)Oo[e]._workInProgressVersionPrimary=null;Oo.length=0}var Gs=Wt.ReactCurrentDispatcher,Ao=Wt.ReactCurrentBatchConfig,Vn=0,se=null,fe=null,ye=null,Sa=!1,vi=!1,Fi=0,tx=0;function Se(){throw Error(M(321))}function Uc(e,t){if(t===null)return!1;for(var n=0;n<t.length&&n<e.length;n++)if(!gt(e[n],t[n]))return!1;return!0}function Yc(e,t,n,r,i,s){if(Vn=s,se=t,t.memoizedState=null,t.updateQueue=null,t.lanes=0,Gs.current=e===null||e.memoizedState===null?sx:ax,e=n(r,i),vi){s=0;do{if(vi=!1,Fi=0,25<=s)throw Error(M(301));s+=1,ye=fe=null,t.updateQueue=null,Gs.current=ox,e=n(r,i)}while(vi)}if(Gs.current=Na,t=fe!==null&&fe.next!==null,Vn=0,ye=fe=se=null,Sa=!1,t)throw Error(M(300));return e}function Xc(){var e=Fi!==0;return Fi=0,e}function wt(){var e={memoizedState:null,baseState:null,baseQueue:null,queue:null,next:null};return ye===null?se.memoizedState=ye=e:ye=ye.next=e,ye}function lt(){if(fe===null){var e=se.alternate;e=e!==null?e.memoizedState:null}else e=fe.next;var t=ye===null?se.memoizedState:ye.next;if(t!==null)ye=t,fe=e;else{if(e===null)throw Error(M(310));fe=e,e={memoizedState:fe.memoizedState,baseState:fe.baseState,baseQueue:fe.baseQueue,queue:fe.queue,next:null},ye===null?se.memoizedState=ye=e:ye=ye.next=e}return ye}function Bi(e,t){return typeof t=="function"?t(e):t}function Io(e){var t=lt(),n=t.queue;if(n===null)throw Error(M(311));n.lastRenderedReducer=e;var r=fe,i=r.baseQueue,s=n.pending;if(s!==null){if(i!==null){var a=i.next;i.next=s.next,s.next=a}r.baseQueue=i=s,n.pending=null}if(i!==null){s=i.next,r=r.baseState;var o=a=null,l=null,u=s;do{var d=u.lane;if((Vn&d)===d)l!==null&&(l=l.next={lane:0,action:u.action,hasEagerState:u.hasEagerState,eagerState:u.eagerState,next:null}),r=u.hasEagerState?u.eagerState:e(r,u.action);else{var h={lane:d,action:u.action,hasEagerState:u.hasEagerState,eagerState:u.eagerState,next:null};l===null?(o=l=h,a=r):l=l.next=h,se.lanes|=d,Un|=d}u=u.next}while(u!==null&&u!==s);l===null?a=r:l.next=o,gt(r,t.memoizedState)||(We=!0),t.memoizedState=r,t.baseState=a,t.baseQueue=l,n.lastRenderedState=r}if(e=n.interleaved,e!==null){i=e;do s=i.lane,se.lanes|=s,Un|=s,i=i.next;while(i!==e)}else i===null&&(n.lanes=0);return[t.memoizedState,n.dispatch]}function Fo(e){var t=lt(),n=t.queue;if(n===null)throw Error(M(311));n.lastRenderedReducer=e;var r=n.dispatch,i=n.pending,s=t.memoizedState;if(i!==null){n.pending=null;var a=i=i.next;do s=e(s,a.action),a=a.next;while(a!==i);gt(s,t.memoizedState)||(We=!0),t.memoizedState=s,t.baseQueue===null&&(t.baseState=s),n.lastRenderedState=s}return[s,r]}function Bp(){}function $p(e,t){var n=se,r=lt(),i=t(),s=!gt(r.memoizedState,i);if(s&&(r.memoizedState=i,We=!0),r=r.queue,Kc(Vp.bind(null,n,r,e),[e]),r.getSnapshot!==t||s||ye!==null&&ye.memoizedState.tag&1){if(n.flags|=2048,$i(9,Wp.bind(null,n,r,i,t),void 0,null),xe===null)throw Error(M(349));Vn&30||Hp(n,t,i)}return i}function Hp(e,t,n){e.flags|=16384,e={getSnapshot:t,value:n},t=se.updateQueue,t===null?(t={lastEffect:null,stores:null},se.updateQueue=t,t.stores=[e]):(n=t.stores,n===null?t.stores=[e]:n.push(e))}function Wp(e,t,n,r){t.value=n,t.getSnapshot=r,Up(t)&&Yp(e)}function Vp(e,t,n){return n(function(){Up(t)&&Yp(e)})}function Up(e){var t=e.getSnapshot;e=e.value;try{var n=t();return!gt(e,n)}catch{return!0}}function Yp(e){var t=$t(e,1);t!==null&&mt(t,e,1,-1)}function bd(e){var t=wt();return typeof e=="function"&&(e=e()),t.memoizedState=t.baseState=e,e={pending:null,interleaved:null,lanes:0,dispatch:null,lastRenderedReducer:Bi,lastRenderedState:e},t.queue=e,e=e.dispatch=ix.bind(null,se,e),[t.memoizedState,e]}function $i(e,t,n,r){return e={tag:e,create:t,destroy:n,deps:r,next:null},t=se.updateQueue,t===null?(t={lastEffect:null,stores:null},se.updateQueue=t,t.lastEffect=e.next=e):(n=t.lastEffect,n===null?t.lastEffect=e.next=e:(r=n.next,n.next=e,e.next=r,t.lastEffect=e)),e}function Xp(){return lt().memoizedState}function Zs(e,t,n,r){var i=wt();se.flags|=e,i.memoizedState=$i(1|t,n,void 0,r===void 0?null:r)}function Ja(e,t,n,r){var i=lt();r=r===void 0?null:r;var s=void 0;if(fe!==null){var a=fe.memoizedState;if(s=a.destroy,r!==null&&Uc(r,a.deps)){i.memoizedState=$i(t,n,s,r);return}}se.flags|=e,i.memoizedState=$i(1|t,n,s,r)}function kd(e,t){return Zs(8390656,8,e,t)}function Kc(e,t){return Ja(2048,8,e,t)}function Kp(e,t){return Ja(4,2,e,t)}function Qp(e,t){return Ja(4,4,e,t)}function Gp(e,t){if(typeof t=="function")return e=e(),t(e),function(){t(null)};if(t!=null)return e=e(),t.current=e,function(){t.current=null}}function Zp(e,t,n){return n=n!=null?n.concat([e]):null,Ja(4,4,Gp.bind(null,t,e),n)}function Qc(){}function qp(e,t){var n=lt();t=t===void 0?null:t;var r=n.memoizedState;return r!==null&&t!==null&&Uc(t,r[1])?r[0]:(n.memoizedState=[e,t],e)}function Jp(e,t){var n=lt();t=t===void 0?null:t;var r=n.memoizedState;return r!==null&&t!==null&&Uc(t,r[1])?r[0]:(e=e(),n.memoizedState=[e,t],e)}function em(e,t,n){return Vn&21?(gt(n,t)||(n=sp(),se.lanes|=n,Un|=n,e.baseState=!0),t):(e.baseState&&(e.baseState=!1,We=!0),e.memoizedState=n)}function nx(e,t){var n=X;X=n!==0&&4>n?n:4,e(!0);var r=Ao.transition;Ao.transition={};try{e(!1),t()}finally{X=n,Ao.transition=r}}function tm(){return lt().memoizedState}function rx(e,t,n){var r=dn(e);if(n={lane:r,action:n,hasEagerState:!1,eagerState:null,next:null},nm(e))rm(t,n);else if(n=Ap(e,t,n,r),n!==null){var i=Ae();mt(n,e,r,i),im(n,t,r)}}function ix(e,t,n){var r=dn(e),i={lane:r,action:n,hasEagerState:!1,eagerState:null,next:null};if(nm(e))rm(t,i);else{var s=e.alternate;if(e.lanes===0&&(s===null||s.lanes===0)&&(s=t.lastRenderedReducer,s!==null))try{var a=t.lastRenderedState,o=s(a,n);if(i.hasEagerState=!0,i.eagerState=o,gt(o,a)){var l=t.interleaved;l===null?(i.next=i,Bc(t)):(i.next=l.next,l.next=i),t.interleaved=i;return}}catch{}finally{}n=Ap(e,t,i,r),n!==null&&(i=Ae(),mt(n,e,r,i),im(n,t,r))}}function nm(e){var t=e.alternate;return e===se||t!==null&&t===se}function rm(e,t){vi=Sa=!0;var n=e.pending;n===null?t.next=t:(t.next=n.next,n.next=t),e.pending=t}function im(e,t,n){if(n&4194240){var r=t.lanes;r&=e.pendingLanes,n|=r,t.lanes=n,Nc(e,n)}}var Na={readContext:ot,useCallback:Se,useContext:Se,useEffect:Se,useImperativeHandle:Se,useInsertionEffect:Se,useLayoutEffect:Se,useMemo:Se,useReducer:Se,useRef:Se,useState:Se,useDebugValue:Se,useDeferredValue:Se,useTransition:Se,useMutableSource:Se,useSyncExternalStore:Se,useId:Se,unstable_isNewReconciler:!1},sx={readContext:ot,useCallback:function(e,t){return wt().memoizedState=[e,t===void 0?null:t],e},useContext:ot,useEffect:kd,useImperativeHandle:function(e,t,n){return n=n!=null?n.concat([e]):null,Zs(4194308,4,Gp.bind(null,t,e),n)},useLayoutEffect:function(e,t){return Zs(4194308,4,e,t)},useInsertionEffect:function(e,t){return Zs(4,2,e,t)},useMemo:function(e,t){var n=wt();return t=t===void 0?null:t,e=e(),n.memoizedState=[e,t],e},useReducer:function(e,t,n){var r=wt();return t=n!==void 0?n(t):t,r.memoizedState=r.baseState=t,e={pending:null,interleaved:null,lanes:0,dispatch:null,lastRenderedReducer:e,lastRenderedState:t},r.queue=e,e=e.dispatch=rx.bind(null,se,e),[r.memoizedState,e]},useRef:function(e){var t=wt();return e={current:e},t.memoizedState=e},useState:bd,useDebugValue:Qc,useDeferredValue:function(e){return wt().memoizedState=e},useTransition:function(){var e=bd(!1),t=e[0];return e=nx.bind(null,e[1]),wt().memoizedState=e,[t,e]},useMutableSource:function(){},useSyncExternalStore:function(e,t,n){var r=se,i=wt();if(re){if(n===void 0)throw Error(M(407));n=n()}else{if(n=t(),xe===null)throw Error(M(349));Vn&30||Hp(r,t,n)}i.memoizedState=n;var s={value:n,getSnapshot:t};return i.queue=s,kd(Vp.bind(null,r,s,e),[e]),r.flags|=2048,$i(9,Wp.bind(null,r,s,n,t),void 0,null),n},useId:function(){var e=wt(),t=xe.identifierPrefix;if(re){var n=Ot,r=Lt;n=(r&~(1<<32-pt(r)-1)).toString(32)+n,t=":"+t+"R"+n,n=Fi++,0<n&&(t+="H"+n.toString(32)),t+=":"}else n=tx++,t=":"+t+"r"+n.toString(32)+":";return e.memoizedState=t},unstable_isNewReconciler:!1},ax={readContext:ot,useCallback:qp,useContext:ot,useEffect:Kc,useImperativeHandle:Zp,useInsertionEffect:Kp,useLayoutEffect:Qp,useMemo:Jp,useReducer:Io,useRef:Xp,useState:function(){return Io(Bi)},useDebugValue:Qc,useDeferredValue:function(e){var t=lt();return em(t,fe.memoizedState,e)},useTransition:function(){var e=Io(Bi)[0],t=lt().memoizedState;return[e,t]},useMutableSource:Bp,useSyncExternalStore:$p,useId:tm,unstable_isNewReconciler:!1},ox={readContext:ot,useCallback:qp,useContext:ot,useEffect:Kc,useImperativeHandle:Zp,useInsertionEffect:Kp,useLayoutEffect:Qp,useMemo:Jp,useReducer:Fo,useRef:Xp,useState:function(){return Fo(Bi)},useDebugValue:Qc,useDeferredValue:function(e){var t=lt();return fe===null?t.memoizedState=e:em(t,fe.memoizedState,e)},useTransition:function(){var e=Fo(Bi)[0],t=lt().memoizedState;return[e,t]},useMutableSource:Bp,useSyncExternalStore:$p,useId:tm,unstable_isNewReconciler:!1};function dt(e,t){if(e&&e.defaultProps){t=ae({},t),e=e.defaultProps;for(var n in e)t[n]===void 0&&(t[n]=e[n]);return t}return t}function Fl(e,t,n,r){t=e.memoizedState,n=n(r,t),n=n==null?t:ae({},t,n),e.memoizedState=n,e.lanes===0&&(e.updateQueue.baseState=n)}var eo={isMounted:function(e){return(e=e._reactInternals)?Gn(e)===e:!1},enqueueSetState:function(e,t,n){e=e._reactInternals;var r=Ae(),i=dn(e),s=It(r,i);s.payload=t,n!=null&&(s.callback=n),t=cn(e,s,i),t!==null&&(mt(t,e,i,r),Qs(t,e,i))},enqueueReplaceState:function(e,t,n){e=e._reactInternals;var r=Ae(),i=dn(e),s=It(r,i);s.tag=1,s.payload=t,n!=null&&(s.callback=n),t=cn(e,s,i),t!==null&&(mt(t,e,i,r),Qs(t,e,i))},enqueueForceUpdate:function(e,t){e=e._reactInternals;var n=Ae(),r=dn(e),i=It(n,r);i.tag=2,t!=null&&(i.callback=t),t=cn(e,i,r),t!==null&&(mt(t,e,r,n),Qs(t,e,r))}};function wd(e,t,n,r,i,s,a){return e=e.stateNode,typeof e.shouldComponentUpdate=="function"?e.shouldComponentUpdate(r,s,a):t.prototype&&t.prototype.isPureReactComponent?!Di(n,r)||!Di(i,s):!0}function sm(e,t,n){var r=!1,i=mn,s=t.contextType;return typeof s=="object"&&s!==null?s=ot(s):(i=Ye(t)?Hn:ze.current,r=t.contextTypes,s=(r=r!=null)?Sr(e,i):mn),t=new t(n,s),e.memoizedState=t.state!==null&&t.state!==void 0?t.state:null,t.updater=eo,e.stateNode=t,t._reactInternals=e,r&&(e=e.stateNode,e.__reactInternalMemoizedUnmaskedChildContext=i,e.__reactInternalMemoizedMaskedChildContext=s),t}function _d(e,t,n,r){e=t.state,typeof t.componentWillReceiveProps=="function"&&t.componentWillReceiveProps(n,r),typeof t.UNSAFE_componentWillReceiveProps=="function"&&t.UNSAFE_componentWillReceiveProps(n,r),t.state!==e&&eo.enqueueReplaceState(t,t.state,null)}function Bl(e,t,n,r){var i=e.stateNode;i.props=n,i.state=e.memoizedState,i.refs={},$c(e);var s=t.contextType;typeof s=="object"&&s!==null?i.context=ot(s):(s=Ye(t)?Hn:ze.current,i.context=Sr(e,s)),i.state=e.memoizedState,s=t.getDerivedStateFromProps,typeof s=="function"&&(Fl(e,t,s,n),i.state=e.memoizedState),typeof t.getDerivedStateFromProps=="function"||typeof i.getSnapshotBeforeUpdate=="function"||typeof i.UNSAFE_componentWillMount!="function"&&typeof i.componentWillMount!="function"||(t=i.state,typeof i.componentWillMount=="function"&&i.componentWillMount(),typeof i.UNSAFE_componentWillMount=="function"&&i.UNSAFE_componentWillMount(),t!==i.state&&eo.enqueueReplaceState(i,i.state,null),_a(e,n,i,r),i.state=e.memoizedState),typeof i.componentDidMount=="function"&&(e.flags|=4194308)}function Pr(e,t){try{var n="",r=t;do n+=Lv(r),r=r.return;while(r);var i=n}catch(s){i=`
Error generating stack: `+s.message+`
`+s.stack}return{value:e,source:t,stack:i,digest:null}}function Bo(e,t,n){return{value:e,source:null,stack:n??null,digest:t??null}}function $l(e,t){try{console.error(t.value)}catch(n){setTimeout(function(){throw n})}}var lx=typeof WeakMap=="function"?WeakMap:Map;function am(e,t,n){n=It(-1,n),n.tag=3,n.payload={element:null};var r=t.value;return n.callback=function(){Ma||(Ma=!0,Zl=r),$l(e,t)},n}function om(e,t,n){n=It(-1,n),n.tag=3;var r=e.type.getDerivedStateFromError;if(typeof r=="function"){var i=t.value;n.payload=function(){return r(i)},n.callback=function(){$l(e,t)}}var s=e.stateNode;return s!==null&&typeof s.componentDidCatch=="function"&&(n.callback=function(){$l(e,t),typeof r!="function"&&(un===null?un=new Set([this]):un.add(this));var a=t.stack;this.componentDidCatch(t.value,{componentStack:a!==null?a:""})}),n}function jd(e,t,n){var r=e.pingCache;if(r===null){r=e.pingCache=new lx;var i=new Set;r.set(t,i)}else i=r.get(t),i===void 0&&(i=new Set,r.set(t,i));i.has(n)||(i.add(n),e=wx.bind(null,e,t,n),t.then(e,e))}function Sd(e){do{var t;if((t=e.tag===13)&&(t=e.memoizedState,t=t!==null?t.dehydrated!==null:!0),t)return e;e=e.return}while(e!==null);return null}function Nd(e,t,n,r,i){return e.mode&1?(e.flags|=65536,e.lanes=i,e):(e===t?e.flags|=65536:(e.flags|=128,n.flags|=131072,n.flags&=-52805,n.tag===1&&(n.alternate===null?n.tag=17:(t=It(-1,1),t.tag=2,cn(n,t,1))),n.lanes|=1),e)}var cx=Wt.ReactCurrentOwner,We=!1;function Oe(e,t,n,r){t.child=e===null?Op(t,null,n,r):Cr(t,e.child,n,r)}function Cd(e,t,n,r,i){n=n.render;var s=t.ref;return yr(t,i),r=Yc(e,t,n,r,s,i),n=Xc(),e!==null&&!We?(t.updateQueue=e.updateQueue,t.flags&=-2053,e.lanes&=~i,Ht(e,t,i)):(re&&n&&Rc(t),t.flags|=1,Oe(e,t,r,i),t.child)}function Md(e,t,n,r,i){if(e===null){var s=n.type;return typeof s=="function"&&!ru(s)&&s.defaultProps===void 0&&n.compare===null&&n.defaultProps===void 0?(t.tag=15,t.type=s,lm(e,t,s,r,i)):(e=ta(n.type,null,r,t,t.mode,i),e.ref=t.ref,e.return=t,t.child=e)}if(s=e.child,!(e.lanes&i)){var a=s.memoizedProps;if(n=n.compare,n=n!==null?n:Di,n(a,r)&&e.ref===t.ref)return Ht(e,t,i)}return t.flags|=1,e=hn(s,r),e.ref=t.ref,e.return=t,t.child=e}function lm(e,t,n,r,i){if(e!==null){var s=e.memoizedProps;if(Di(s,r)&&e.ref===t.ref)if(We=!1,t.pendingProps=r=s,(e.lanes&i)!==0)e.flags&131072&&(We=!0);else return t.lanes=e.lanes,Ht(e,t,i)}return Hl(e,t,n,r,i)}function cm(e,t,n){var r=t.pendingProps,i=r.children,s=e!==null?e.memoizedState:null;if(r.mode==="hidden")if(!(t.mode&1))t.memoizedState={baseLanes:0,cachePool:null,transitions:null},G(fr,Ke),Ke|=n;else{if(!(n&1073741824))return e=s!==null?s.baseLanes|n:n,t.lanes=t.childLanes=1073741824,t.memoizedState={baseLanes:e,cachePool:null,transitions:null},t.updateQueue=null,G(fr,Ke),Ke|=e,null;t.memoizedState={baseLanes:0,cachePool:null,transitions:null},r=s!==null?s.baseLanes:n,G(fr,Ke),Ke|=r}else s!==null?(r=s.baseLanes|n,t.memoizedState=null):r=n,G(fr,Ke),Ke|=r;return Oe(e,t,i,n),t.child}function um(e,t){var n=t.ref;(e===null&&n!==null||e!==null&&e.ref!==n)&&(t.flags|=512,t.flags|=2097152)}function Hl(e,t,n,r,i){var s=Ye(n)?Hn:ze.current;return s=Sr(t,s),yr(t,i),n=Yc(e,t,n,r,s,i),r=Xc(),e!==null&&!We?(t.updateQueue=e.updateQueue,t.flags&=-2053,e.lanes&=~i,Ht(e,t,i)):(re&&r&&Rc(t),t.flags|=1,Oe(e,t,n,i),t.child)}function Pd(e,t,n,r,i){if(Ye(n)){var s=!0;ya(t)}else s=!1;if(yr(t,i),t.stateNode===null)qs(e,t),sm(t,n,r),Bl(t,n,r,i),r=!0;else if(e===null){var a=t.stateNode,o=t.memoizedProps;a.props=o;var l=a.context,u=n.contextType;typeof u=="object"&&u!==null?u=ot(u):(u=Ye(n)?Hn:ze.current,u=Sr(t,u));var d=n.getDerivedStateFromProps,h=typeof d=="function"||typeof a.getSnapshotBeforeUpdate=="function";h||typeof a.UNSAFE_componentWillReceiveProps!="function"&&typeof a.componentWillReceiveProps!="function"||(o!==r||l!==u)&&_d(t,a,r,u),Kt=!1;var f=t.memoizedState;a.state=f,_a(t,r,a,i),l=t.memoizedState,o!==r||f!==l||Ue.current||Kt?(typeof d=="function"&&(Fl(t,n,d,r),l=t.memoizedState),(o=Kt||wd(t,n,o,r,f,l,u))?(h||typeof a.UNSAFE_componentWillMount!="function"&&typeof a.componentWillMount!="function"||(typeof a.componentWillMount=="function"&&a.componentWillMount(),typeof a.UNSAFE_componentWillMount=="function"&&a.UNSAFE_componentWillMount()),typeof a.componentDidMount=="function"&&(t.flags|=4194308)):(typeof a.componentDidMount=="function"&&(t.flags|=4194308),t.memoizedProps=r,t.memoizedState=l),a.props=r,a.state=l,a.context=u,r=o):(typeof a.componentDidMount=="function"&&(t.flags|=4194308),r=!1)}else{a=t.stateNode,Ip(e,t),o=t.memoizedProps,u=t.type===t.elementType?o:dt(t.type,o),a.props=u,h=t.pendingProps,f=a.context,l=n.contextType,typeof l=="object"&&l!==null?l=ot(l):(l=Ye(n)?Hn:ze.current,l=Sr(t,l));var p=n.getDerivedStateFromProps;(d=typeof p=="function"||typeof a.getSnapshotBeforeUpdate=="function")||typeof a.UNSAFE_componentWillReceiveProps!="function"&&typeof a.componentWillReceiveProps!="function"||(o!==h||f!==l)&&_d(t,a,r,l),Kt=!1,f=t.memoizedState,a.state=f,_a(t,r,a,i);var m=t.memoizedState;o!==h||f!==m||Ue.current||Kt?(typeof p=="function"&&(Fl(t,n,p,r),m=t.memoizedState),(u=Kt||wd(t,n,u,r,f,m,l)||!1)?(d||typeof a.UNSAFE_componentWillUpdate!="function"&&typeof a.componentWillUpdate!="function"||(typeof a.componentWillUpdate=="function"&&a.componentWillUpdate(r,m,l),typeof a.UNSAFE_componentWillUpdate=="function"&&a.UNSAFE_componentWillUpdate(r,m,l)),typeof a.componentDidUpdate=="function"&&(t.flags|=4),typeof a.getSnapshotBeforeUpdate=="function"&&(t.flags|=1024)):(typeof a.componentDidUpdate!="function"||o===e.memoizedProps&&f===e.memoizedState||(t.flags|=4),typeof a.getSnapshotBeforeUpdate!="function"||o===e.memoizedProps&&f===e.memoizedState||(t.flags|=1024),t.memoizedProps=r,t.memoizedState=m),a.props=r,a.state=m,a.context=l,r=u):(typeof a.componentDidUpdate!="function"||o===e.memoizedProps&&f===e.memoizedState||(t.flags|=4),typeof a.getSnapshotBeforeUpdate!="function"||o===e.memoizedProps&&f===e.memoizedState||(t.flags|=1024),r=!1)}return Wl(e,t,n,r,s,i)}function Wl(e,t,n,r,i,s){um(e,t);var a=(t.flags&128)!==0;if(!r&&!a)return i&&pd(t,n,!1),Ht(e,t,s);r=t.stateNode,cx.current=t;var o=a&&typeof n.getDerivedStateFromError!="function"?null:r.render();return t.flags|=1,e!==null&&a?(t.child=Cr(t,e.child,null,s),t.child=Cr(t,null,o,s)):Oe(e,t,o,s),t.memoizedState=r.state,i&&pd(t,n,!0),t.child}function dm(e){var t=e.stateNode;t.pendingContext?fd(e,t.pendingContext,t.pendingContext!==t.context):t.context&&fd(e,t.context,!1),Hc(e,t.containerInfo)}function Ed(e,t,n,r,i){return Nr(),Oc(i),t.flags|=256,Oe(e,t,n,r),t.child}var Vl={dehydrated:null,treeContext:null,retryLane:0};function Ul(e){return{baseLanes:e,cachePool:null,transitions:null}}function hm(e,t,n){var r=t.pendingProps,i=ie.current,s=!1,a=(t.flags&128)!==0,o;if((o=a)||(o=e!==null&&e.memoizedState===null?!1:(i&2)!==0),o?(s=!0,t.flags&=-129):(e===null||e.memoizedState!==null)&&(i|=1),G(ie,i&1),e===null)return Al(t),e=t.memoizedState,e!==null&&(e=e.dehydrated,e!==null)?(t.mode&1?e.data==="$!"?t.lanes=8:t.lanes=1073741824:t.lanes=1,null):(a=r.children,e=r.fallback,s?(r=t.mode,s=t.child,a={mode:"hidden",children:a},!(r&1)&&s!==null?(s.childLanes=0,s.pendingProps=a):s=ro(a,r,0,null),e=On(e,r,n,null),s.return=t,e.return=t,s.sibling=e,t.child=s,t.child.memoizedState=Ul(n),t.memoizedState=Vl,e):Gc(t,a));if(i=e.memoizedState,i!==null&&(o=i.dehydrated,o!==null))return ux(e,t,a,r,o,i,n);if(s){s=r.fallback,a=t.mode,i=e.child,o=i.sibling;var l={mode:"hidden",children:r.children};return!(a&1)&&t.child!==i?(r=t.child,r.childLanes=0,r.pendingProps=l,t.deletions=null):(r=hn(i,l),r.subtreeFlags=i.subtreeFlags&14680064),o!==null?s=hn(o,s):(s=On(s,a,n,null),s.flags|=2),s.return=t,r.return=t,r.sibling=s,t.child=r,r=s,s=t.child,a=e.child.memoizedState,a=a===null?Ul(n):{baseLanes:a.baseLanes|n,cachePool:null,transitions:a.transitions},s.memoizedState=a,s.childLanes=e.childLanes&~n,t.memoizedState=Vl,r}return s=e.child,e=s.sibling,r=hn(s,{mode:"visible",children:r.children}),!(t.mode&1)&&(r.lanes=n),r.return=t,r.sibling=null,e!==null&&(n=t.deletions,n===null?(t.deletions=[e],t.flags|=16):n.push(e)),t.child=r,t.memoizedState=null,r}function Gc(e,t){return t=ro({mode:"visible",children:t},e.mode,0,null),t.return=e,e.child=t}function Cs(e,t,n,r){return r!==null&&Oc(r),Cr(t,e.child,null,n),e=Gc(t,t.pendingProps.children),e.flags|=2,t.memoizedState=null,e}function ux(e,t,n,r,i,s,a){if(n)return t.flags&256?(t.flags&=-257,r=Bo(Error(M(422))),Cs(e,t,a,r)):t.memoizedState!==null?(t.child=e.child,t.flags|=128,null):(s=r.fallback,i=t.mode,r=ro({mode:"visible",children:r.children},i,0,null),s=On(s,i,a,null),s.flags|=2,r.return=t,s.return=t,r.sibling=s,t.child=r,t.mode&1&&Cr(t,e.child,null,a),t.child.memoizedState=Ul(a),t.memoizedState=Vl,s);if(!(t.mode&1))return Cs(e,t,a,null);if(i.data==="$!"){if(r=i.nextSibling&&i.nextSibling.dataset,r)var o=r.dgst;return r=o,s=Error(M(419)),r=Bo(s,r,void 0),Cs(e,t,a,r)}if(o=(a&e.childLanes)!==0,We||o){if(r=xe,r!==null){switch(a&-a){case 4:i=2;break;case 16:i=8;break;case 64:case 128:case 256:case 512:case 1024:case 2048:case 4096:case 8192:case 16384:case 32768:case 65536:case 131072:case 262144:case 524288:case 1048576:case 2097152:case 4194304:case 8388608:case 16777216:case 33554432:case 67108864:i=32;break;case 536870912:i=268435456;break;default:i=0}i=i&(r.suspendedLanes|a)?0:i,i!==0&&i!==s.retryLane&&(s.retryLane=i,$t(e,i),mt(r,e,i,-1))}return nu(),r=Bo(Error(M(421))),Cs(e,t,a,r)}return i.data==="$?"?(t.flags|=128,t.child=e.child,t=_x.bind(null,e),i._reactRetry=t,null):(e=s.treeContext,Ge=ln(i.nextSibling),Ze=t,re=!0,ft=null,e!==null&&(nt[rt++]=Lt,nt[rt++]=Ot,nt[rt++]=Wn,Lt=e.id,Ot=e.overflow,Wn=t),t=Gc(t,r.children),t.flags|=4096,t)}function Td(e,t,n){e.lanes|=t;var r=e.alternate;r!==null&&(r.lanes|=t),Il(e.return,t,n)}function $o(e,t,n,r,i){var s=e.memoizedState;s===null?e.memoizedState={isBackwards:t,rendering:null,renderingStartTime:0,last:r,tail:n,tailMode:i}:(s.isBackwards=t,s.rendering=null,s.renderingStartTime=0,s.last=r,s.tail=n,s.tailMode=i)}function fm(e,t,n){var r=t.pendingProps,i=r.revealOrder,s=r.tail;if(Oe(e,t,r.children,n),r=ie.current,r&2)r=r&1|2,t.flags|=128;else{if(e!==null&&e.flags&128)e:for(e=t.child;e!==null;){if(e.tag===13)e.memoizedState!==null&&Td(e,n,t);else if(e.tag===19)Td(e,n,t);else if(e.child!==null){e.child.return=e,e=e.child;continue}if(e===t)break e;for(;e.sibling===null;){if(e.return===null||e.return===t)break e;e=e.return}e.sibling.return=e.return,e=e.sibling}r&=1}if(G(ie,r),!(t.mode&1))t.memoizedState=null;else switch(i){case"forwards":for(n=t.child,i=null;n!==null;)e=n.alternate,e!==null&&ja(e)===null&&(i=n),n=n.sibling;n=i,n===null?(i=t.child,t.child=null):(i=n.sibling,n.sibling=null),$o(t,!1,i,n,s);break;case"backwards":for(n=null,i=t.child,t.child=null;i!==null;){if(e=i.alternate,e!==null&&ja(e)===null){t.child=i;break}e=i.sibling,i.sibling=n,n=i,i=e}$o(t,!0,n,null,s);break;case"together":$o(t,!1,null,null,void 0);break;default:t.memoizedState=null}return t.child}function qs(e,t){!(t.mode&1)&&e!==null&&(e.alternate=null,t.alternate=null,t.flags|=2)}function Ht(e,t,n){if(e!==null&&(t.dependencies=e.dependencies),Un|=t.lanes,!(n&t.childLanes))return null;if(e!==null&&t.child!==e.child)throw Error(M(153));if(t.child!==null){for(e=t.child,n=hn(e,e.pendingProps),t.child=n,n.return=t;e.sibling!==null;)e=e.sibling,n=n.sibling=hn(e,e.pendingProps),n.return=t;n.sibling=null}return t.child}function dx(e,t,n){switch(t.tag){case 3:dm(t),Nr();break;case 5:Fp(t);break;case 1:Ye(t.type)&&ya(t);break;case 4:Hc(t,t.stateNode.containerInfo);break;case 10:var r=t.type._context,i=t.memoizedProps.value;G(ka,r._currentValue),r._currentValue=i;break;case 13:if(r=t.memoizedState,r!==null)return r.dehydrated!==null?(G(ie,ie.current&1),t.flags|=128,null):n&t.child.childLanes?hm(e,t,n):(G(ie,ie.current&1),e=Ht(e,t,n),e!==null?e.sibling:null);G(ie,ie.current&1);break;case 19:if(r=(n&t.childLanes)!==0,e.flags&128){if(r)return fm(e,t,n);t.flags|=128}if(i=t.memoizedState,i!==null&&(i.rendering=null,i.tail=null,i.lastEffect=null),G(ie,ie.current),r)break;return null;case 22:case 23:return t.lanes=0,cm(e,t,n)}return Ht(e,t,n)}var pm,Yl,mm,gm;pm=function(e,t){for(var n=t.child;n!==null;){if(n.tag===5||n.tag===6)e.appendChild(n.stateNode);else if(n.tag!==4&&n.child!==null){n.child.return=n,n=n.child;continue}if(n===t)break;for(;n.sibling===null;){if(n.return===null||n.return===t)return;n=n.return}n.sibling.return=n.return,n=n.sibling}};Yl=function(){};mm=function(e,t,n,r){var i=e.memoizedProps;if(i!==r){e=t.stateNode,Tn(Nt.current);var s=null;switch(n){case"input":i=pl(e,i),r=pl(e,r),s=[];break;case"select":i=ae({},i,{value:void 0}),r=ae({},r,{value:void 0}),s=[];break;case"textarea":i=vl(e,i),r=vl(e,r),s=[];break;default:typeof i.onClick!="function"&&typeof r.onClick=="function"&&(e.onclick=ga)}xl(n,r);var a;n=null;for(u in i)if(!r.hasOwnProperty(u)&&i.hasOwnProperty(u)&&i[u]!=null)if(u==="style"){var o=i[u];for(a in o)o.hasOwnProperty(a)&&(n||(n={}),n[a]="")}else u!=="dangerouslySetInnerHTML"&&u!=="children"&&u!=="suppressContentEditableWarning"&&u!=="suppressHydrationWarning"&&u!=="autoFocus"&&(Ni.hasOwnProperty(u)?s||(s=[]):(s=s||[]).push(u,null));for(u in r){var l=r[u];if(o=i!=null?i[u]:void 0,r.hasOwnProperty(u)&&l!==o&&(l!=null||o!=null))if(u==="style")if(o){for(a in o)!o.hasOwnProperty(a)||l&&l.hasOwnProperty(a)||(n||(n={}),n[a]="");for(a in l)l.hasOwnProperty(a)&&o[a]!==l[a]&&(n||(n={}),n[a]=l[a])}else n||(s||(s=[]),s.push(u,n)),n=l;else u==="dangerouslySetInnerHTML"?(l=l?l.__html:void 0,o=o?o.__html:void 0,l!=null&&o!==l&&(s=s||[]).push(u,l)):u==="children"?typeof l!="string"&&typeof l!="number"||(s=s||[]).push(u,""+l):u!=="suppressContentEditableWarning"&&u!=="suppressHydrationWarning"&&(Ni.hasOwnProperty(u)?(l!=null&&u==="onScroll"&&ee("scroll",e),s||o===l||(s=[])):(s=s||[]).push(u,l))}n&&(s=s||[]).push("style",n);var u=s;(t.updateQueue=u)&&(t.flags|=4)}};gm=function(e,t,n,r){n!==r&&(t.flags|=4)};function Gr(e,t){if(!re)switch(e.tailMode){case"hidden":t=e.tail;for(var n=null;t!==null;)t.alternate!==null&&(n=t),t=t.sibling;n===null?e.tail=null:n.sibling=null;break;case"collapsed":n=e.tail;for(var r=null;n!==null;)n.alternate!==null&&(r=n),n=n.sibling;r===null?t||e.tail===null?e.tail=null:e.tail.sibling=null:r.sibling=null}}function Ne(e){var t=e.alternate!==null&&e.alternate.child===e.child,n=0,r=0;if(t)for(var i=e.child;i!==null;)n|=i.lanes|i.childLanes,r|=i.subtreeFlags&14680064,r|=i.flags&14680064,i.return=e,i=i.sibling;else for(i=e.child;i!==null;)n|=i.lanes|i.childLanes,r|=i.subtreeFlags,r|=i.flags,i.return=e,i=i.sibling;return e.subtreeFlags|=r,e.childLanes=n,t}function hx(e,t,n){var r=t.pendingProps;switch(Lc(t),t.tag){case 2:case 16:case 15:case 0:case 11:case 7:case 8:case 12:case 9:case 14:return Ne(t),null;case 1:return Ye(t.type)&&va(),Ne(t),null;case 3:return r=t.stateNode,Mr(),ne(Ue),ne(ze),Vc(),r.pendingContext&&(r.context=r.pendingContext,r.pendingContext=null),(e===null||e.child===null)&&(Ss(t)?t.flags|=4:e===null||e.memoizedState.isDehydrated&&!(t.flags&256)||(t.flags|=1024,ft!==null&&(ec(ft),ft=null))),Yl(e,t),Ne(t),null;case 5:Wc(t);var i=Tn(Ii.current);if(n=t.type,e!==null&&t.stateNode!=null)mm(e,t,n,r,i),e.ref!==t.ref&&(t.flags|=512,t.flags|=2097152);else{if(!r){if(t.stateNode===null)throw Error(M(166));return Ne(t),null}if(e=Tn(Nt.current),Ss(t)){r=t.stateNode,n=t.type;var s=t.memoizedProps;switch(r[jt]=t,r[Oi]=s,e=(t.mode&1)!==0,n){case"dialog":ee("cancel",r),ee("close",r);break;case"iframe":case"object":case"embed":ee("load",r);break;case"video":case"audio":for(i=0;i<ai.length;i++)ee(ai[i],r);break;case"source":ee("error",r);break;case"img":case"image":case"link":ee("error",r),ee("load",r);break;case"details":ee("toggle",r);break;case"input":Bu(r,s),ee("invalid",r);break;case"select":r._wrapperState={wasMultiple:!!s.multiple},ee("invalid",r);break;case"textarea":Hu(r,s),ee("invalid",r)}xl(n,s),i=null;for(var a in s)if(s.hasOwnProperty(a)){var o=s[a];a==="children"?typeof o=="string"?r.textContent!==o&&(s.suppressHydrationWarning!==!0&&js(r.textContent,o,e),i=["children",o]):typeof o=="number"&&r.textContent!==""+o&&(s.suppressHydrationWarning!==!0&&js(r.textContent,o,e),i=["children",""+o]):Ni.hasOwnProperty(a)&&o!=null&&a==="onScroll"&&ee("scroll",r)}switch(n){case"input":gs(r),$u(r,s,!0);break;case"textarea":gs(r),Wu(r);break;case"select":case"option":break;default:typeof s.onClick=="function"&&(r.onclick=ga)}r=i,t.updateQueue=r,r!==null&&(t.flags|=4)}else{a=i.nodeType===9?i:i.ownerDocument,e==="http://www.w3.org/1999/xhtml"&&(e=Vf(n)),e==="http://www.w3.org/1999/xhtml"?n==="script"?(e=a.createElement("div"),e.innerHTML="<script><\/script>",e=e.removeChild(e.firstChild)):typeof r.is=="string"?e=a.createElement(n,{is:r.is}):(e=a.createElement(n),n==="select"&&(a=e,r.multiple?a.multiple=!0:r.size&&(a.size=r.size))):e=a.createElementNS(e,n),e[jt]=t,e[Oi]=r,pm(e,t,!1,!1),t.stateNode=e;e:{switch(a=bl(n,r),n){case"dialog":ee("cancel",e),ee("close",e),i=r;break;case"iframe":case"object":case"embed":ee("load",e),i=r;break;case"video":case"audio":for(i=0;i<ai.length;i++)ee(ai[i],e);i=r;break;case"source":ee("error",e),i=r;break;case"img":case"image":case"link":ee("error",e),ee("load",e),i=r;break;case"details":ee("toggle",e),i=r;break;case"input":Bu(e,r),i=pl(e,r),ee("invalid",e);break;case"option":i=r;break;case"select":e._wrapperState={wasMultiple:!!r.multiple},i=ae({},r,{value:void 0}),ee("invalid",e);break;case"textarea":Hu(e,r),i=vl(e,r),ee("invalid",e);break;default:i=r}xl(n,i),o=i;for(s in o)if(o.hasOwnProperty(s)){var l=o[s];s==="style"?Xf(e,l):s==="dangerouslySetInnerHTML"?(l=l?l.__html:void 0,l!=null&&Uf(e,l)):s==="children"?typeof l=="string"?(n!=="textarea"||l!=="")&&Ci(e,l):typeof l=="number"&&Ci(e,""+l):s!=="suppressContentEditableWarning"&&s!=="suppressHydrationWarning"&&s!=="autoFocus"&&(Ni.hasOwnProperty(s)?l!=null&&s==="onScroll"&&ee("scroll",e):l!=null&&bc(e,s,l,a))}switch(n){case"input":gs(e),$u(e,r,!1);break;case"textarea":gs(e),Wu(e);break;case"option":r.value!=null&&e.setAttribute("value",""+pn(r.value));break;case"select":e.multiple=!!r.multiple,s=r.value,s!=null?pr(e,!!r.multiple,s,!1):r.defaultValue!=null&&pr(e,!!r.multiple,r.defaultValue,!0);break;default:typeof i.onClick=="function"&&(e.onclick=ga)}switch(n){case"button":case"input":case"select":case"textarea":r=!!r.autoFocus;break e;case"img":r=!0;break e;default:r=!1}}r&&(t.flags|=4)}t.ref!==null&&(t.flags|=512,t.flags|=2097152)}return Ne(t),null;case 6:if(e&&t.stateNode!=null)gm(e,t,e.memoizedProps,r);else{if(typeof r!="string"&&t.stateNode===null)throw Error(M(166));if(n=Tn(Ii.current),Tn(Nt.current),Ss(t)){if(r=t.stateNode,n=t.memoizedProps,r[jt]=t,(s=r.nodeValue!==n)&&(e=Ze,e!==null))switch(e.tag){case 3:js(r.nodeValue,n,(e.mode&1)!==0);break;case 5:e.memoizedProps.suppressHydrationWarning!==!0&&js(r.nodeValue,n,(e.mode&1)!==0)}s&&(t.flags|=4)}else r=(n.nodeType===9?n:n.ownerDocument).createTextNode(r),r[jt]=t,t.stateNode=r}return Ne(t),null;case 13:if(ne(ie),r=t.memoizedState,e===null||e.memoizedState!==null&&e.memoizedState.dehydrated!==null){if(re&&Ge!==null&&t.mode&1&&!(t.flags&128))Rp(),Nr(),t.flags|=98560,s=!1;else if(s=Ss(t),r!==null&&r.dehydrated!==null){if(e===null){if(!s)throw Error(M(318));if(s=t.memoizedState,s=s!==null?s.dehydrated:null,!s)throw Error(M(317));s[jt]=t}else Nr(),!(t.flags&128)&&(t.memoizedState=null),t.flags|=4;Ne(t),s=!1}else ft!==null&&(ec(ft),ft=null),s=!0;if(!s)return t.flags&65536?t:null}return t.flags&128?(t.lanes=n,t):(r=r!==null,r!==(e!==null&&e.memoizedState!==null)&&r&&(t.child.flags|=8192,t.mode&1&&(e===null||ie.current&1?me===0&&(me=3):nu())),t.updateQueue!==null&&(t.flags|=4),Ne(t),null);case 4:return Mr(),Yl(e,t),e===null&&Ri(t.stateNode.containerInfo),Ne(t),null;case 10:return Fc(t.type._context),Ne(t),null;case 17:return Ye(t.type)&&va(),Ne(t),null;case 19:if(ne(ie),s=t.memoizedState,s===null)return Ne(t),null;if(r=(t.flags&128)!==0,a=s.rendering,a===null)if(r)Gr(s,!1);else{if(me!==0||e!==null&&e.flags&128)for(e=t.child;e!==null;){if(a=ja(e),a!==null){for(t.flags|=128,Gr(s,!1),r=a.updateQueue,r!==null&&(t.updateQueue=r,t.flags|=4),t.subtreeFlags=0,r=n,n=t.child;n!==null;)s=n,e=r,s.flags&=14680066,a=s.alternate,a===null?(s.childLanes=0,s.lanes=e,s.child=null,s.subtreeFlags=0,s.memoizedProps=null,s.memoizedState=null,s.updateQueue=null,s.dependencies=null,s.stateNode=null):(s.childLanes=a.childLanes,s.lanes=a.lanes,s.child=a.child,s.subtreeFlags=0,s.deletions=null,s.memoizedProps=a.memoizedProps,s.memoizedState=a.memoizedState,s.updateQueue=a.updateQueue,s.type=a.type,e=a.dependencies,s.dependencies=e===null?null:{lanes:e.lanes,firstContext:e.firstContext}),n=n.sibling;return G(ie,ie.current&1|2),t.child}e=e.sibling}s.tail!==null&&ce()>Er&&(t.flags|=128,r=!0,Gr(s,!1),t.lanes=4194304)}else{if(!r)if(e=ja(a),e!==null){if(t.flags|=128,r=!0,n=e.updateQueue,n!==null&&(t.updateQueue=n,t.flags|=4),Gr(s,!0),s.tail===null&&s.tailMode==="hidden"&&!a.alternate&&!re)return Ne(t),null}else 2*ce()-s.renderingStartTime>Er&&n!==1073741824&&(t.flags|=128,r=!0,Gr(s,!1),t.lanes=4194304);s.isBackwards?(a.sibling=t.child,t.child=a):(n=s.last,n!==null?n.sibling=a:t.child=a,s.last=a)}return s.tail!==null?(t=s.tail,s.rendering=t,s.tail=t.sibling,s.renderingStartTime=ce(),t.sibling=null,n=ie.current,G(ie,r?n&1|2:n&1),t):(Ne(t),null);case 22:case 23:return tu(),r=t.memoizedState!==null,e!==null&&e.memoizedState!==null!==r&&(t.flags|=8192),r&&t.mode&1?Ke&1073741824&&(Ne(t),t.subtreeFlags&6&&(t.flags|=8192)):Ne(t),null;case 24:return null;case 25:return null}throw Error(M(156,t.tag))}function fx(e,t){switch(Lc(t),t.tag){case 1:return Ye(t.type)&&va(),e=t.flags,e&65536?(t.flags=e&-65537|128,t):null;case 3:return Mr(),ne(Ue),ne(ze),Vc(),e=t.flags,e&65536&&!(e&128)?(t.flags=e&-65537|128,t):null;case 5:return Wc(t),null;case 13:if(ne(ie),e=t.memoizedState,e!==null&&e.dehydrated!==null){if(t.alternate===null)throw Error(M(340));Nr()}return e=t.flags,e&65536?(t.flags=e&-65537|128,t):null;case 19:return ne(ie),null;case 4:return Mr(),null;case 10:return Fc(t.type._context),null;case 22:case 23:return tu(),null;case 24:return null;default:return null}}var Ms=!1,Me=!1,px=typeof WeakSet=="function"?WeakSet:Set,z=null;function hr(e,t){var n=e.ref;if(n!==null)if(typeof n=="function")try{n(null)}catch(r){oe(e,t,r)}else n.current=null}function Xl(e,t,n){try{n()}catch(r){oe(e,t,r)}}var zd=!1;function mx(e,t){if(El=fa,e=kp(),Dc(e)){if("selectionStart"in e)var n={start:e.selectionStart,end:e.selectionEnd};else e:{n=(n=e.ownerDocument)&&n.defaultView||window;var r=n.getSelection&&n.getSelection();if(r&&r.rangeCount!==0){n=r.anchorNode;var i=r.anchorOffset,s=r.focusNode;r=r.focusOffset;try{n.nodeType,s.nodeType}catch{n=null;break e}var a=0,o=-1,l=-1,u=0,d=0,h=e,f=null;t:for(;;){for(var p;h!==n||i!==0&&h.nodeType!==3||(o=a+i),h!==s||r!==0&&h.nodeType!==3||(l=a+r),h.nodeType===3&&(a+=h.nodeValue.length),(p=h.firstChild)!==null;)f=h,h=p;for(;;){if(h===e)break t;if(f===n&&++u===i&&(o=a),f===s&&++d===r&&(l=a),(p=h.nextSibling)!==null)break;h=f,f=h.parentNode}h=p}n=o===-1||l===-1?null:{start:o,end:l}}else n=null}n=n||{start:0,end:0}}else n=null;for(Tl={focusedElem:e,selectionRange:n},fa=!1,z=t;z!==null;)if(t=z,e=t.child,(t.subtreeFlags&1028)!==0&&e!==null)e.return=t,z=e;else for(;z!==null;){t=z;try{var m=t.alternate;if(t.flags&1024)switch(t.tag){case 0:case 11:case 15:break;case 1:if(m!==null){var v=m.memoizedProps,y=m.memoizedState,g=t.stateNode,x=g.getSnapshotBeforeUpdate(t.elementType===t.type?v:dt(t.type,v),y);g.__reactInternalSnapshotBeforeUpdate=x}break;case 3:var b=t.stateNode.containerInfo;b.nodeType===1?b.textContent="":b.nodeType===9&&b.documentElement&&b.removeChild(b.documentElement);break;case 5:case 6:case 4:case 17:break;default:throw Error(M(163))}}catch(k){oe(t,t.return,k)}if(e=t.sibling,e!==null){e.return=t.return,z=e;break}z=t.return}return m=zd,zd=!1,m}function yi(e,t,n){var r=t.updateQueue;if(r=r!==null?r.lastEffect:null,r!==null){var i=r=r.next;do{if((i.tag&e)===e){var s=i.destroy;i.destroy=void 0,s!==void 0&&Xl(t,n,s)}i=i.next}while(i!==r)}}function to(e,t){if(t=t.updateQueue,t=t!==null?t.lastEffect:null,t!==null){var n=t=t.next;do{if((n.tag&e)===e){var r=n.create;n.destroy=r()}n=n.next}while(n!==t)}}function Kl(e){var t=e.ref;if(t!==null){var n=e.stateNode;switch(e.tag){case 5:e=n;break;default:e=n}typeof t=="function"?t(e):t.current=e}}function vm(e){var t=e.alternate;t!==null&&(e.alternate=null,vm(t)),e.child=null,e.deletions=null,e.sibling=null,e.tag===5&&(t=e.stateNode,t!==null&&(delete t[jt],delete t[Oi],delete t[Rl],delete t[Zy],delete t[qy])),e.stateNode=null,e.return=null,e.dependencies=null,e.memoizedProps=null,e.memoizedState=null,e.pendingProps=null,e.stateNode=null,e.updateQueue=null}function ym(e){return e.tag===5||e.tag===3||e.tag===4}function Dd(e){e:for(;;){for(;e.sibling===null;){if(e.return===null||ym(e.return))return null;e=e.return}for(e.sibling.return=e.return,e=e.sibling;e.tag!==5&&e.tag!==6&&e.tag!==18;){if(e.flags&2||e.child===null||e.tag===4)continue e;e.child.return=e,e=e.child}if(!(e.flags&2))return e.stateNode}}function Ql(e,t,n){var r=e.tag;if(r===5||r===6)e=e.stateNode,t?n.nodeType===8?n.parentNode.insertBefore(e,t):n.insertBefore(e,t):(n.nodeType===8?(t=n.parentNode,t.insertBefore(e,n)):(t=n,t.appendChild(e)),n=n._reactRootContainer,n!=null||t.onclick!==null||(t.onclick=ga));else if(r!==4&&(e=e.child,e!==null))for(Ql(e,t,n),e=e.sibling;e!==null;)Ql(e,t,n),e=e.sibling}function Gl(e,t,n){var r=e.tag;if(r===5||r===6)e=e.stateNode,t?n.insertBefore(e,t):n.appendChild(e);else if(r!==4&&(e=e.child,e!==null))for(Gl(e,t,n),e=e.sibling;e!==null;)Gl(e,t,n),e=e.sibling}var ke=null,ht=!1;function Vt(e,t,n){for(n=n.child;n!==null;)xm(e,t,n),n=n.sibling}function xm(e,t,n){if(St&&typeof St.onCommitFiberUnmount=="function")try{St.onCommitFiberUnmount(Xa,n)}catch{}switch(n.tag){case 5:Me||hr(n,t);case 6:var r=ke,i=ht;ke=null,Vt(e,t,n),ke=r,ht=i,ke!==null&&(ht?(e=ke,n=n.stateNode,e.nodeType===8?e.parentNode.removeChild(n):e.removeChild(n)):ke.removeChild(n.stateNode));break;case 18:ke!==null&&(ht?(e=ke,n=n.stateNode,e.nodeType===8?Ro(e.parentNode,n):e.nodeType===1&&Ro(e,n),Ti(e)):Ro(ke,n.stateNode));break;case 4:r=ke,i=ht,ke=n.stateNode.containerInfo,ht=!0,Vt(e,t,n),ke=r,ht=i;break;case 0:case 11:case 14:case 15:if(!Me&&(r=n.updateQueue,r!==null&&(r=r.lastEffect,r!==null))){i=r=r.next;do{var s=i,a=s.destroy;s=s.tag,a!==void 0&&(s&2||s&4)&&Xl(n,t,a),i=i.next}while(i!==r)}Vt(e,t,n);break;case 1:if(!Me&&(hr(n,t),r=n.stateNode,typeof r.componentWillUnmount=="function"))try{r.props=n.memoizedProps,r.state=n.memoizedState,r.componentWillUnmount()}catch(o){oe(n,t,o)}Vt(e,t,n);break;case 21:Vt(e,t,n);break;case 22:n.mode&1?(Me=(r=Me)||n.memoizedState!==null,Vt(e,t,n),Me=r):Vt(e,t,n);break;default:Vt(e,t,n)}}function Rd(e){var t=e.updateQueue;if(t!==null){e.updateQueue=null;var n=e.stateNode;n===null&&(n=e.stateNode=new px),t.forEach(function(r){var i=jx.bind(null,e,r);n.has(r)||(n.add(r),r.then(i,i))})}}function ut(e,t){var n=t.deletions;if(n!==null)for(var r=0;r<n.length;r++){var i=n[r];try{var s=e,a=t,o=a;e:for(;o!==null;){switch(o.tag){case 5:ke=o.stateNode,ht=!1;break e;case 3:ke=o.stateNode.containerInfo,ht=!0;break e;case 4:ke=o.stateNode.containerInfo,ht=!0;break e}o=o.return}if(ke===null)throw Error(M(160));xm(s,a,i),ke=null,ht=!1;var l=i.alternate;l!==null&&(l.return=null),i.return=null}catch(u){oe(i,t,u)}}if(t.subtreeFlags&12854)for(t=t.child;t!==null;)bm(t,e),t=t.sibling}function bm(e,t){var n=e.alternate,r=e.flags;switch(e.tag){case 0:case 11:case 14:case 15:if(ut(t,e),xt(e),r&4){try{yi(3,e,e.return),to(3,e)}catch(v){oe(e,e.return,v)}try{yi(5,e,e.return)}catch(v){oe(e,e.return,v)}}break;case 1:ut(t,e),xt(e),r&512&&n!==null&&hr(n,n.return);break;case 5:if(ut(t,e),xt(e),r&512&&n!==null&&hr(n,n.return),e.flags&32){var i=e.stateNode;try{Ci(i,"")}catch(v){oe(e,e.return,v)}}if(r&4&&(i=e.stateNode,i!=null)){var s=e.memoizedProps,a=n!==null?n.memoizedProps:s,o=e.type,l=e.updateQueue;if(e.updateQueue=null,l!==null)try{o==="input"&&s.type==="radio"&&s.name!=null&&Hf(i,s),bl(o,a);var u=bl(o,s);for(a=0;a<l.length;a+=2){var d=l[a],h=l[a+1];d==="style"?Xf(i,h):d==="dangerouslySetInnerHTML"?Uf(i,h):d==="children"?Ci(i,h):bc(i,d,h,u)}switch(o){case"input":ml(i,s);break;case"textarea":Wf(i,s);break;case"select":var f=i._wrapperState.wasMultiple;i._wrapperState.wasMultiple=!!s.multiple;var p=s.value;p!=null?pr(i,!!s.multiple,p,!1):f!==!!s.multiple&&(s.defaultValue!=null?pr(i,!!s.multiple,s.defaultValue,!0):pr(i,!!s.multiple,s.multiple?[]:"",!1))}i[Oi]=s}catch(v){oe(e,e.return,v)}}break;case 6:if(ut(t,e),xt(e),r&4){if(e.stateNode===null)throw Error(M(162));i=e.stateNode,s=e.memoizedProps;try{i.nodeValue=s}catch(v){oe(e,e.return,v)}}break;case 3:if(ut(t,e),xt(e),r&4&&n!==null&&n.memoizedState.isDehydrated)try{Ti(t.containerInfo)}catch(v){oe(e,e.return,v)}break;case 4:ut(t,e),xt(e);break;case 13:ut(t,e),xt(e),i=e.child,i.flags&8192&&(s=i.memoizedState!==null,i.stateNode.isHidden=s,!s||i.alternate!==null&&i.alternate.memoizedState!==null||(Jc=ce())),r&4&&Rd(e);break;case 22:if(d=n!==null&&n.memoizedState!==null,e.mode&1?(Me=(u=Me)||d,ut(t,e),Me=u):ut(t,e),xt(e),r&8192){if(u=e.memoizedState!==null,(e.stateNode.isHidden=u)&&!d&&e.mode&1)for(z=e,d=e.child;d!==null;){for(h=z=d;z!==null;){switch(f=z,p=f.child,f.tag){case 0:case 11:case 14:case 15:yi(4,f,f.return);break;case 1:hr(f,f.return);var m=f.stateNode;if(typeof m.componentWillUnmount=="function"){r=f,n=f.return;try{t=r,m.props=t.memoizedProps,m.state=t.memoizedState,m.componentWillUnmount()}catch(v){oe(r,n,v)}}break;case 5:hr(f,f.return);break;case 22:if(f.memoizedState!==null){Od(h);continue}}p!==null?(p.return=f,z=p):Od(h)}d=d.sibling}e:for(d=null,h=e;;){if(h.tag===5){if(d===null){d=h;try{i=h.stateNode,u?(s=i.style,typeof s.setProperty=="function"?s.setProperty("display","none","important"):s.display="none"):(o=h.stateNode,l=h.memoizedProps.style,a=l!=null&&l.hasOwnProperty("display")?l.display:null,o.style.display=Yf("display",a))}catch(v){oe(e,e.return,v)}}}else if(h.tag===6){if(d===null)try{h.stateNode.nodeValue=u?"":h.memoizedProps}catch(v){oe(e,e.return,v)}}else if((h.tag!==22&&h.tag!==23||h.memoizedState===null||h===e)&&h.child!==null){h.child.return=h,h=h.child;continue}if(h===e)break e;for(;h.sibling===null;){if(h.return===null||h.return===e)break e;d===h&&(d=null),h=h.return}d===h&&(d=null),h.sibling.return=h.return,h=h.sibling}}break;case 19:ut(t,e),xt(e),r&4&&Rd(e);break;case 21:break;default:ut(t,e),xt(e)}}function xt(e){var t=e.flags;if(t&2){try{e:{for(var n=e.return;n!==null;){if(ym(n)){var r=n;break e}n=n.return}throw Error(M(160))}switch(r.tag){case 5:var i=r.stateNode;r.flags&32&&(Ci(i,""),r.flags&=-33);var s=Dd(e);Gl(e,s,i);break;case 3:case 4:var a=r.stateNode.containerInfo,o=Dd(e);Ql(e,o,a);break;default:throw Error(M(161))}}catch(l){oe(e,e.return,l)}e.flags&=-3}t&4096&&(e.flags&=-4097)}function gx(e,t,n){z=e,km(e)}function km(e,t,n){for(var r=(e.mode&1)!==0;z!==null;){var i=z,s=i.child;if(i.tag===22&&r){var a=i.memoizedState!==null||Ms;if(!a){var o=i.alternate,l=o!==null&&o.memoizedState!==null||Me;o=Ms;var u=Me;if(Ms=a,(Me=l)&&!u)for(z=i;z!==null;)a=z,l=a.child,a.tag===22&&a.memoizedState!==null?Ad(i):l!==null?(l.return=a,z=l):Ad(i);for(;s!==null;)z=s,km(s),s=s.sibling;z=i,Ms=o,Me=u}Ld(e)}else i.subtreeFlags&8772&&s!==null?(s.return=i,z=s):Ld(e)}}function Ld(e){for(;z!==null;){var t=z;if(t.flags&8772){var n=t.alternate;try{if(t.flags&8772)switch(t.tag){case 0:case 11:case 15:Me||to(5,t);break;case 1:var r=t.stateNode;if(t.flags&4&&!Me)if(n===null)r.componentDidMount();else{var i=t.elementType===t.type?n.memoizedProps:dt(t.type,n.memoizedProps);r.componentDidUpdate(i,n.memoizedState,r.__reactInternalSnapshotBeforeUpdate)}var s=t.updateQueue;s!==null&&xd(t,s,r);break;case 3:var a=t.updateQueue;if(a!==null){if(n=null,t.child!==null)switch(t.child.tag){case 5:n=t.child.stateNode;break;case 1:n=t.child.stateNode}xd(t,a,n)}break;case 5:var o=t.stateNode;if(n===null&&t.flags&4){n=o;var l=t.memoizedProps;switch(t.type){case"button":case"input":case"select":case"textarea":l.autoFocus&&n.focus();break;case"img":l.src&&(n.src=l.src)}}break;case 6:break;case 4:break;case 12:break;case 13:if(t.memoizedState===null){var u=t.alternate;if(u!==null){var d=u.memoizedState;if(d!==null){var h=d.dehydrated;h!==null&&Ti(h)}}}break;case 19:case 17:case 21:case 22:case 23:case 25:break;default:throw Error(M(163))}Me||t.flags&512&&Kl(t)}catch(f){oe(t,t.return,f)}}if(t===e){z=null;break}if(n=t.sibling,n!==null){n.return=t.return,z=n;break}z=t.return}}function Od(e){for(;z!==null;){var t=z;if(t===e){z=null;break}var n=t.sibling;if(n!==null){n.return=t.return,z=n;break}z=t.return}}function Ad(e){for(;z!==null;){var t=z;try{switch(t.tag){case 0:case 11:case 15:var n=t.return;try{to(4,t)}catch(l){oe(t,n,l)}break;case 1:var r=t.stateNode;if(typeof r.componentDidMount=="function"){var i=t.return;try{r.componentDidMount()}catch(l){oe(t,i,l)}}var s=t.return;try{Kl(t)}catch(l){oe(t,s,l)}break;case 5:var a=t.return;try{Kl(t)}catch(l){oe(t,a,l)}}}catch(l){oe(t,t.return,l)}if(t===e){z=null;break}var o=t.sibling;if(o!==null){o.return=t.return,z=o;break}z=t.return}}var vx=Math.ceil,Ca=Wt.ReactCurrentDispatcher,Zc=Wt.ReactCurrentOwner,at=Wt.ReactCurrentBatchConfig,H=0,xe=null,de=null,_e=0,Ke=0,fr=xn(0),me=0,Hi=null,Un=0,no=0,qc=0,xi=null,$e=null,Jc=0,Er=1/0,zt=null,Ma=!1,Zl=null,un=null,Ps=!1,qt=null,Pa=0,bi=0,ql=null,Js=-1,ea=0;function Ae(){return H&6?ce():Js!==-1?Js:Js=ce()}function dn(e){return e.mode&1?H&2&&_e!==0?_e&-_e:ex.transition!==null?(ea===0&&(ea=sp()),ea):(e=X,e!==0||(e=window.event,e=e===void 0?16:hp(e.type)),e):1}function mt(e,t,n,r){if(50<bi)throw bi=0,ql=null,Error(M(185));ts(e,n,r),(!(H&2)||e!==xe)&&(e===xe&&(!(H&2)&&(no|=n),me===4&&Gt(e,_e)),Xe(e,r),n===1&&H===0&&!(t.mode&1)&&(Er=ce()+500,qa&&bn()))}function Xe(e,t){var n=e.callbackNode;ey(e,t);var r=ha(e,e===xe?_e:0);if(r===0)n!==null&&Yu(n),e.callbackNode=null,e.callbackPriority=0;else if(t=r&-r,e.callbackPriority!==t){if(n!=null&&Yu(n),t===1)e.tag===0?Jy(Id.bind(null,e)):Tp(Id.bind(null,e)),Qy(function(){!(H&6)&&bn()}),n=null;else{switch(ap(r)){case 1:n=Sc;break;case 4:n=rp;break;case 16:n=da;break;case 536870912:n=ip;break;default:n=da}n=Pm(n,wm.bind(null,e))}e.callbackPriority=t,e.callbackNode=n}}function wm(e,t){if(Js=-1,ea=0,H&6)throw Error(M(327));var n=e.callbackNode;if(xr()&&e.callbackNode!==n)return null;var r=ha(e,e===xe?_e:0);if(r===0)return null;if(r&30||r&e.expiredLanes||t)t=Ea(e,r);else{t=r;var i=H;H|=2;var s=jm();(xe!==e||_e!==t)&&(zt=null,Er=ce()+500,Ln(e,t));do try{bx();break}catch(o){_m(e,o)}while(!0);Ic(),Ca.current=s,H=i,de!==null?t=0:(xe=null,_e=0,t=me)}if(t!==0){if(t===2&&(i=Sl(e),i!==0&&(r=i,t=Jl(e,i))),t===1)throw n=Hi,Ln(e,0),Gt(e,r),Xe(e,ce()),n;if(t===6)Gt(e,r);else{if(i=e.current.alternate,!(r&30)&&!yx(i)&&(t=Ea(e,r),t===2&&(s=Sl(e),s!==0&&(r=s,t=Jl(e,s))),t===1))throw n=Hi,Ln(e,0),Gt(e,r),Xe(e,ce()),n;switch(e.finishedWork=i,e.finishedLanes=r,t){case 0:case 1:throw Error(M(345));case 2:Nn(e,$e,zt);break;case 3:if(Gt(e,r),(r&130023424)===r&&(t=Jc+500-ce(),10<t)){if(ha(e,0)!==0)break;if(i=e.suspendedLanes,(i&r)!==r){Ae(),e.pingedLanes|=e.suspendedLanes&i;break}e.timeoutHandle=Dl(Nn.bind(null,e,$e,zt),t);break}Nn(e,$e,zt);break;case 4:if(Gt(e,r),(r&4194240)===r)break;for(t=e.eventTimes,i=-1;0<r;){var a=31-pt(r);s=1<<a,a=t[a],a>i&&(i=a),r&=~s}if(r=i,r=ce()-r,r=(120>r?120:480>r?480:1080>r?1080:1920>r?1920:3e3>r?3e3:4320>r?4320:1960*vx(r/1960))-r,10<r){e.timeoutHandle=Dl(Nn.bind(null,e,$e,zt),r);break}Nn(e,$e,zt);break;case 5:Nn(e,$e,zt);break;default:throw Error(M(329))}}}return Xe(e,ce()),e.callbackNode===n?wm.bind(null,e):null}function Jl(e,t){var n=xi;return e.current.memoizedState.isDehydrated&&(Ln(e,t).flags|=256),e=Ea(e,t),e!==2&&(t=$e,$e=n,t!==null&&ec(t)),e}function ec(e){$e===null?$e=e:$e.push.apply($e,e)}function yx(e){for(var t=e;;){if(t.flags&16384){var n=t.updateQueue;if(n!==null&&(n=n.stores,n!==null))for(var r=0;r<n.length;r++){var i=n[r],s=i.getSnapshot;i=i.value;try{if(!gt(s(),i))return!1}catch{return!1}}}if(n=t.child,t.subtreeFlags&16384&&n!==null)n.return=t,t=n;else{if(t===e)break;for(;t.sibling===null;){if(t.return===null||t.return===e)return!0;t=t.return}t.sibling.return=t.return,t=t.sibling}}return!0}function Gt(e,t){for(t&=~qc,t&=~no,e.suspendedLanes|=t,e.pingedLanes&=~t,e=e.expirationTimes;0<t;){var n=31-pt(t),r=1<<n;e[n]=-1,t&=~r}}function Id(e){if(H&6)throw Error(M(327));xr();var t=ha(e,0);if(!(t&1))return Xe(e,ce()),null;var n=Ea(e,t);if(e.tag!==0&&n===2){var r=Sl(e);r!==0&&(t=r,n=Jl(e,r))}if(n===1)throw n=Hi,Ln(e,0),Gt(e,t),Xe(e,ce()),n;if(n===6)throw Error(M(345));return e.finishedWork=e.current.alternate,e.finishedLanes=t,Nn(e,$e,zt),Xe(e,ce()),null}function eu(e,t){var n=H;H|=1;try{return e(t)}finally{H=n,H===0&&(Er=ce()+500,qa&&bn())}}function Yn(e){qt!==null&&qt.tag===0&&!(H&6)&&xr();var t=H;H|=1;var n=at.transition,r=X;try{if(at.transition=null,X=1,e)return e()}finally{X=r,at.transition=n,H=t,!(H&6)&&bn()}}function tu(){Ke=fr.current,ne(fr)}function Ln(e,t){e.finishedWork=null,e.finishedLanes=0;var n=e.timeoutHandle;if(n!==-1&&(e.timeoutHandle=-1,Ky(n)),de!==null)for(n=de.return;n!==null;){var r=n;switch(Lc(r),r.tag){case 1:r=r.type.childContextTypes,r!=null&&va();break;case 3:Mr(),ne(Ue),ne(ze),Vc();break;case 5:Wc(r);break;case 4:Mr();break;case 13:ne(ie);break;case 19:ne(ie);break;case 10:Fc(r.type._context);break;case 22:case 23:tu()}n=n.return}if(xe=e,de=e=hn(e.current,null),_e=Ke=t,me=0,Hi=null,qc=no=Un=0,$e=xi=null,En!==null){for(t=0;t<En.length;t++)if(n=En[t],r=n.interleaved,r!==null){n.interleaved=null;var i=r.next,s=n.pending;if(s!==null){var a=s.next;s.next=i,r.next=a}n.pending=r}En=null}return e}function _m(e,t){do{var n=de;try{if(Ic(),Gs.current=Na,Sa){for(var r=se.memoizedState;r!==null;){var i=r.queue;i!==null&&(i.pending=null),r=r.next}Sa=!1}if(Vn=0,ye=fe=se=null,vi=!1,Fi=0,Zc.current=null,n===null||n.return===null){me=1,Hi=t,de=null;break}e:{var s=e,a=n.return,o=n,l=t;if(t=_e,o.flags|=32768,l!==null&&typeof l=="object"&&typeof l.then=="function"){var u=l,d=o,h=d.tag;if(!(d.mode&1)&&(h===0||h===11||h===15)){var f=d.alternate;f?(d.updateQueue=f.updateQueue,d.memoizedState=f.memoizedState,d.lanes=f.lanes):(d.updateQueue=null,d.memoizedState=null)}var p=Sd(a);if(p!==null){p.flags&=-257,Nd(p,a,o,s,t),p.mode&1&&jd(s,u,t),t=p,l=u;var m=t.updateQueue;if(m===null){var v=new Set;v.add(l),t.updateQueue=v}else m.add(l);break e}else{if(!(t&1)){jd(s,u,t),nu();break e}l=Error(M(426))}}else if(re&&o.mode&1){var y=Sd(a);if(y!==null){!(y.flags&65536)&&(y.flags|=256),Nd(y,a,o,s,t),Oc(Pr(l,o));break e}}s=l=Pr(l,o),me!==4&&(me=2),xi===null?xi=[s]:xi.push(s),s=a;do{switch(s.tag){case 3:s.flags|=65536,t&=-t,s.lanes|=t;var g=am(s,l,t);yd(s,g);break e;case 1:o=l;var x=s.type,b=s.stateNode;if(!(s.flags&128)&&(typeof x.getDerivedStateFromError=="function"||b!==null&&typeof b.componentDidCatch=="function"&&(un===null||!un.has(b)))){s.flags|=65536,t&=-t,s.lanes|=t;var k=om(s,o,t);yd(s,k);break e}}s=s.return}while(s!==null)}Nm(n)}catch(w){t=w,de===n&&n!==null&&(de=n=n.return);continue}break}while(!0)}function jm(){var e=Ca.current;return Ca.current=Na,e===null?Na:e}function nu(){(me===0||me===3||me===2)&&(me=4),xe===null||!(Un&268435455)&&!(no&268435455)||Gt(xe,_e)}function Ea(e,t){var n=H;H|=2;var r=jm();(xe!==e||_e!==t)&&(zt=null,Ln(e,t));do try{xx();break}catch(i){_m(e,i)}while(!0);if(Ic(),H=n,Ca.current=r,de!==null)throw Error(M(261));return xe=null,_e=0,me}function xx(){for(;de!==null;)Sm(de)}function bx(){for(;de!==null&&!Uv();)Sm(de)}function Sm(e){var t=Mm(e.alternate,e,Ke);e.memoizedProps=e.pendingProps,t===null?Nm(e):de=t,Zc.current=null}function Nm(e){var t=e;do{var n=t.alternate;if(e=t.return,t.flags&32768){if(n=fx(n,t),n!==null){n.flags&=32767,de=n;return}if(e!==null)e.flags|=32768,e.subtreeFlags=0,e.deletions=null;else{me=6,de=null;return}}else if(n=hx(n,t,Ke),n!==null){de=n;return}if(t=t.sibling,t!==null){de=t;return}de=t=e}while(t!==null);me===0&&(me=5)}function Nn(e,t,n){var r=X,i=at.transition;try{at.transition=null,X=1,kx(e,t,n,r)}finally{at.transition=i,X=r}return null}function kx(e,t,n,r){do xr();while(qt!==null);if(H&6)throw Error(M(327));n=e.finishedWork;var i=e.finishedLanes;if(n===null)return null;if(e.finishedWork=null,e.finishedLanes=0,n===e.current)throw Error(M(177));e.callbackNode=null,e.callbackPriority=0;var s=n.lanes|n.childLanes;if(ty(e,s),e===xe&&(de=xe=null,_e=0),!(n.subtreeFlags&2064)&&!(n.flags&2064)||Ps||(Ps=!0,Pm(da,function(){return xr(),null})),s=(n.flags&15990)!==0,n.subtreeFlags&15990||s){s=at.transition,at.transition=null;var a=X;X=1;var o=H;H|=4,Zc.current=null,mx(e,n),bm(n,e),$y(Tl),fa=!!El,Tl=El=null,e.current=n,gx(n),Yv(),H=o,X=a,at.transition=s}else e.current=n;if(Ps&&(Ps=!1,qt=e,Pa=i),s=e.pendingLanes,s===0&&(un=null),Qv(n.stateNode),Xe(e,ce()),t!==null)for(r=e.onRecoverableError,n=0;n<t.length;n++)i=t[n],r(i.value,{componentStack:i.stack,digest:i.digest});if(Ma)throw Ma=!1,e=Zl,Zl=null,e;return Pa&1&&e.tag!==0&&xr(),s=e.pendingLanes,s&1?e===ql?bi++:(bi=0,ql=e):bi=0,bn(),null}function xr(){if(qt!==null){var e=ap(Pa),t=at.transition,n=X;try{if(at.transition=null,X=16>e?16:e,qt===null)var r=!1;else{if(e=qt,qt=null,Pa=0,H&6)throw Error(M(331));var i=H;for(H|=4,z=e.current;z!==null;){var s=z,a=s.child;if(z.flags&16){var o=s.deletions;if(o!==null){for(var l=0;l<o.length;l++){var u=o[l];for(z=u;z!==null;){var d=z;switch(d.tag){case 0:case 11:case 15:yi(8,d,s)}var h=d.child;if(h!==null)h.return=d,z=h;else for(;z!==null;){d=z;var f=d.sibling,p=d.return;if(vm(d),d===u){z=null;break}if(f!==null){f.return=p,z=f;break}z=p}}}var m=s.alternate;if(m!==null){var v=m.child;if(v!==null){m.child=null;do{var y=v.sibling;v.sibling=null,v=y}while(v!==null)}}z=s}}if(s.subtreeFlags&2064&&a!==null)a.return=s,z=a;else e:for(;z!==null;){if(s=z,s.flags&2048)switch(s.tag){case 0:case 11:case 15:yi(9,s,s.return)}var g=s.sibling;if(g!==null){g.return=s.return,z=g;break e}z=s.return}}var x=e.current;for(z=x;z!==null;){a=z;var b=a.child;if(a.subtreeFlags&2064&&b!==null)b.return=a,z=b;else e:for(a=x;z!==null;){if(o=z,o.flags&2048)try{switch(o.tag){case 0:case 11:case 15:to(9,o)}}catch(w){oe(o,o.return,w)}if(o===a){z=null;break e}var k=o.sibling;if(k!==null){k.return=o.return,z=k;break e}z=o.return}}if(H=i,bn(),St&&typeof St.onPostCommitFiberRoot=="function")try{St.onPostCommitFiberRoot(Xa,e)}catch{}r=!0}return r}finally{X=n,at.transition=t}}return!1}function Fd(e,t,n){t=Pr(n,t),t=am(e,t,1),e=cn(e,t,1),t=Ae(),e!==null&&(ts(e,1,t),Xe(e,t))}function oe(e,t,n){if(e.tag===3)Fd(e,e,n);else for(;t!==null;){if(t.tag===3){Fd(t,e,n);break}else if(t.tag===1){var r=t.stateNode;if(typeof t.type.getDerivedStateFromError=="function"||typeof r.componentDidCatch=="function"&&(un===null||!un.has(r))){e=Pr(n,e),e=om(t,e,1),t=cn(t,e,1),e=Ae(),t!==null&&(ts(t,1,e),Xe(t,e));break}}t=t.return}}function wx(e,t,n){var r=e.pingCache;r!==null&&r.delete(t),t=Ae(),e.pingedLanes|=e.suspendedLanes&n,xe===e&&(_e&n)===n&&(me===4||me===3&&(_e&130023424)===_e&&500>ce()-Jc?Ln(e,0):qc|=n),Xe(e,t)}function Cm(e,t){t===0&&(e.mode&1?(t=xs,xs<<=1,!(xs&130023424)&&(xs=4194304)):t=1);var n=Ae();e=$t(e,t),e!==null&&(ts(e,t,n),Xe(e,n))}function _x(e){var t=e.memoizedState,n=0;t!==null&&(n=t.retryLane),Cm(e,n)}function jx(e,t){var n=0;switch(e.tag){case 13:var r=e.stateNode,i=e.memoizedState;i!==null&&(n=i.retryLane);break;case 19:r=e.stateNode;break;default:throw Error(M(314))}r!==null&&r.delete(t),Cm(e,n)}var Mm;Mm=function(e,t,n){if(e!==null)if(e.memoizedProps!==t.pendingProps||Ue.current)We=!0;else{if(!(e.lanes&n)&&!(t.flags&128))return We=!1,dx(e,t,n);We=!!(e.flags&131072)}else We=!1,re&&t.flags&1048576&&zp(t,ba,t.index);switch(t.lanes=0,t.tag){case 2:var r=t.type;qs(e,t),e=t.pendingProps;var i=Sr(t,ze.current);yr(t,n),i=Yc(null,t,r,e,i,n);var s=Xc();return t.flags|=1,typeof i=="object"&&i!==null&&typeof i.render=="function"&&i.$$typeof===void 0?(t.tag=1,t.memoizedState=null,t.updateQueue=null,Ye(r)?(s=!0,ya(t)):s=!1,t.memoizedState=i.state!==null&&i.state!==void 0?i.state:null,$c(t),i.updater=eo,t.stateNode=i,i._reactInternals=t,Bl(t,r,e,n),t=Wl(null,t,r,!0,s,n)):(t.tag=0,re&&s&&Rc(t),Oe(null,t,i,n),t=t.child),t;case 16:r=t.elementType;e:{switch(qs(e,t),e=t.pendingProps,i=r._init,r=i(r._payload),t.type=r,i=t.tag=Nx(r),e=dt(r,e),i){case 0:t=Hl(null,t,r,e,n);break e;case 1:t=Pd(null,t,r,e,n);break e;case 11:t=Cd(null,t,r,e,n);break e;case 14:t=Md(null,t,r,dt(r.type,e),n);break e}throw Error(M(306,r,""))}return t;case 0:return r=t.type,i=t.pendingProps,i=t.elementType===r?i:dt(r,i),Hl(e,t,r,i,n);case 1:return r=t.type,i=t.pendingProps,i=t.elementType===r?i:dt(r,i),Pd(e,t,r,i,n);case 3:e:{if(dm(t),e===null)throw Error(M(387));r=t.pendingProps,s=t.memoizedState,i=s.element,Ip(e,t),_a(t,r,null,n);var a=t.memoizedState;if(r=a.element,s.isDehydrated)if(s={element:r,isDehydrated:!1,cache:a.cache,pendingSuspenseBoundaries:a.pendingSuspenseBoundaries,transitions:a.transitions},t.updateQueue.baseState=s,t.memoizedState=s,t.flags&256){i=Pr(Error(M(423)),t),t=Ed(e,t,r,n,i);break e}else if(r!==i){i=Pr(Error(M(424)),t),t=Ed(e,t,r,n,i);break e}else for(Ge=ln(t.stateNode.containerInfo.firstChild),Ze=t,re=!0,ft=null,n=Op(t,null,r,n),t.child=n;n;)n.flags=n.flags&-3|4096,n=n.sibling;else{if(Nr(),r===i){t=Ht(e,t,n);break e}Oe(e,t,r,n)}t=t.child}return t;case 5:return Fp(t),e===null&&Al(t),r=t.type,i=t.pendingProps,s=e!==null?e.memoizedProps:null,a=i.children,zl(r,i)?a=null:s!==null&&zl(r,s)&&(t.flags|=32),um(e,t),Oe(e,t,a,n),t.child;case 6:return e===null&&Al(t),null;case 13:return hm(e,t,n);case 4:return Hc(t,t.stateNode.containerInfo),r=t.pendingProps,e===null?t.child=Cr(t,null,r,n):Oe(e,t,r,n),t.child;case 11:return r=t.type,i=t.pendingProps,i=t.elementType===r?i:dt(r,i),Cd(e,t,r,i,n);case 7:return Oe(e,t,t.pendingProps,n),t.child;case 8:return Oe(e,t,t.pendingProps.children,n),t.child;case 12:return Oe(e,t,t.pendingProps.children,n),t.child;case 10:e:{if(r=t.type._context,i=t.pendingProps,s=t.memoizedProps,a=i.value,G(ka,r._currentValue),r._currentValue=a,s!==null)if(gt(s.value,a)){if(s.children===i.children&&!Ue.current){t=Ht(e,t,n);break e}}else for(s=t.child,s!==null&&(s.return=t);s!==null;){var o=s.dependencies;if(o!==null){a=s.child;for(var l=o.firstContext;l!==null;){if(l.context===r){if(s.tag===1){l=It(-1,n&-n),l.tag=2;var u=s.updateQueue;if(u!==null){u=u.shared;var d=u.pending;d===null?l.next=l:(l.next=d.next,d.next=l),u.pending=l}}s.lanes|=n,l=s.alternate,l!==null&&(l.lanes|=n),Il(s.return,n,t),o.lanes|=n;break}l=l.next}}else if(s.tag===10)a=s.type===t.type?null:s.child;else if(s.tag===18){if(a=s.return,a===null)throw Error(M(341));a.lanes|=n,o=a.alternate,o!==null&&(o.lanes|=n),Il(a,n,t),a=s.sibling}else a=s.child;if(a!==null)a.return=s;else for(a=s;a!==null;){if(a===t){a=null;break}if(s=a.sibling,s!==null){s.return=a.return,a=s;break}a=a.return}s=a}Oe(e,t,i.children,n),t=t.child}return t;case 9:return i=t.type,r=t.pendingProps.children,yr(t,n),i=ot(i),r=r(i),t.flags|=1,Oe(e,t,r,n),t.child;case 14:return r=t.type,i=dt(r,t.pendingProps),i=dt(r.type,i),Md(e,t,r,i,n);case 15:return lm(e,t,t.type,t.pendingProps,n);case 17:return r=t.type,i=t.pendingProps,i=t.elementType===r?i:dt(r,i),qs(e,t),t.tag=1,Ye(r)?(e=!0,ya(t)):e=!1,yr(t,n),sm(t,r,i),Bl(t,r,i,n),Wl(null,t,r,!0,e,n);case 19:return fm(e,t,n);case 22:return cm(e,t,n)}throw Error(M(156,t.tag))};function Pm(e,t){return np(e,t)}function Sx(e,t,n,r){this.tag=e,this.key=n,this.sibling=this.child=this.return=this.stateNode=this.type=this.elementType=null,this.index=0,this.ref=null,this.pendingProps=t,this.dependencies=this.memoizedState=this.updateQueue=this.memoizedProps=null,this.mode=r,this.subtreeFlags=this.flags=0,this.deletions=null,this.childLanes=this.lanes=0,this.alternate=null}function it(e,t,n,r){return new Sx(e,t,n,r)}function ru(e){return e=e.prototype,!(!e||!e.isReactComponent)}function Nx(e){if(typeof e=="function")return ru(e)?1:0;if(e!=null){if(e=e.$$typeof,e===wc)return 11;if(e===_c)return 14}return 2}function hn(e,t){var n=e.alternate;return n===null?(n=it(e.tag,t,e.key,e.mode),n.elementType=e.elementType,n.type=e.type,n.stateNode=e.stateNode,n.alternate=e,e.alternate=n):(n.pendingProps=t,n.type=e.type,n.flags=0,n.subtreeFlags=0,n.deletions=null),n.flags=e.flags&14680064,n.childLanes=e.childLanes,n.lanes=e.lanes,n.child=e.child,n.memoizedProps=e.memoizedProps,n.memoizedState=e.memoizedState,n.updateQueue=e.updateQueue,t=e.dependencies,n.dependencies=t===null?null:{lanes:t.lanes,firstContext:t.firstContext},n.sibling=e.sibling,n.index=e.index,n.ref=e.ref,n}function ta(e,t,n,r,i,s){var a=2;if(r=e,typeof e=="function")ru(e)&&(a=1);else if(typeof e=="string")a=5;else e:switch(e){case rr:return On(n.children,i,s,t);case kc:a=8,i|=8;break;case ul:return e=it(12,n,t,i|2),e.elementType=ul,e.lanes=s,e;case dl:return e=it(13,n,t,i),e.elementType=dl,e.lanes=s,e;case hl:return e=it(19,n,t,i),e.elementType=hl,e.lanes=s,e;case Ff:return ro(n,i,s,t);default:if(typeof e=="object"&&e!==null)switch(e.$$typeof){case Af:a=10;break e;case If:a=9;break e;case wc:a=11;break e;case _c:a=14;break e;case Xt:a=16,r=null;break e}throw Error(M(130,e==null?e:typeof e,""))}return t=it(a,n,t,i),t.elementType=e,t.type=r,t.lanes=s,t}function On(e,t,n,r){return e=it(7,e,r,t),e.lanes=n,e}function ro(e,t,n,r){return e=it(22,e,r,t),e.elementType=Ff,e.lanes=n,e.stateNode={isHidden:!1},e}function Ho(e,t,n){return e=it(6,e,null,t),e.lanes=n,e}function Wo(e,t,n){return t=it(4,e.children!==null?e.children:[],e.key,t),t.lanes=n,t.stateNode={containerInfo:e.containerInfo,pendingChildren:null,implementation:e.implementation},t}function Cx(e,t,n,r,i){this.tag=t,this.containerInfo=e,this.finishedWork=this.pingCache=this.current=this.pendingChildren=null,this.timeoutHandle=-1,this.callbackNode=this.pendingContext=this.context=null,this.callbackPriority=0,this.eventTimes=_o(0),this.expirationTimes=_o(-1),this.entangledLanes=this.finishedLanes=this.mutableReadLanes=this.expiredLanes=this.pingedLanes=this.suspendedLanes=this.pendingLanes=0,this.entanglements=_o(0),this.identifierPrefix=r,this.onRecoverableError=i,this.mutableSourceEagerHydrationData=null}function iu(e,t,n,r,i,s,a,o,l){return e=new Cx(e,t,n,o,l),t===1?(t=1,s===!0&&(t|=8)):t=0,s=it(3,null,null,t),e.current=s,s.stateNode=e,s.memoizedState={element:r,isDehydrated:n,cache:null,transitions:null,pendingSuspenseBoundaries:null},$c(s),e}function Mx(e,t,n){var r=3<arguments.length&&arguments[3]!==void 0?arguments[3]:null;return{$$typeof:nr,key:r==null?null:""+r,children:e,containerInfo:t,implementation:n}}function Em(e){if(!e)return mn;e=e._reactInternals;e:{if(Gn(e)!==e||e.tag!==1)throw Error(M(170));var t=e;do{switch(t.tag){case 3:t=t.stateNode.context;break e;case 1:if(Ye(t.type)){t=t.stateNode.__reactInternalMemoizedMergedChildContext;break e}}t=t.return}while(t!==null);throw Error(M(171))}if(e.tag===1){var n=e.type;if(Ye(n))return Ep(e,n,t)}return t}function Tm(e,t,n,r,i,s,a,o,l){return e=iu(n,r,!0,e,i,s,a,o,l),e.context=Em(null),n=e.current,r=Ae(),i=dn(n),s=It(r,i),s.callback=t??null,cn(n,s,i),e.current.lanes=i,ts(e,i,r),Xe(e,r),e}function io(e,t,n,r){var i=t.current,s=Ae(),a=dn(i);return n=Em(n),t.context===null?t.context=n:t.pendingContext=n,t=It(s,a),t.payload={element:e},r=r===void 0?null:r,r!==null&&(t.callback=r),e=cn(i,t,a),e!==null&&(mt(e,i,a,s),Qs(e,i,a)),a}function Ta(e){if(e=e.current,!e.child)return null;switch(e.child.tag){case 5:return e.child.stateNode;default:return e.child.stateNode}}function Bd(e,t){if(e=e.memoizedState,e!==null&&e.dehydrated!==null){var n=e.retryLane;e.retryLane=n!==0&&n<t?n:t}}function su(e,t){Bd(e,t),(e=e.alternate)&&Bd(e,t)}function Px(){return null}var zm=typeof reportError=="function"?reportError:function(e){console.error(e)};function au(e){this._internalRoot=e}so.prototype.render=au.prototype.render=function(e){var t=this._internalRoot;if(t===null)throw Error(M(409));io(e,t,null,null)};so.prototype.unmount=au.prototype.unmount=function(){var e=this._internalRoot;if(e!==null){this._internalRoot=null;var t=e.containerInfo;Yn(function(){io(null,e,null,null)}),t[Bt]=null}};function so(e){this._internalRoot=e}so.prototype.unstable_scheduleHydration=function(e){if(e){var t=cp();e={blockedOn:null,target:e,priority:t};for(var n=0;n<Qt.length&&t!==0&&t<Qt[n].priority;n++);Qt.splice(n,0,e),n===0&&dp(e)}};function ou(e){return!(!e||e.nodeType!==1&&e.nodeType!==9&&e.nodeType!==11)}function ao(e){return!(!e||e.nodeType!==1&&e.nodeType!==9&&e.nodeType!==11&&(e.nodeType!==8||e.nodeValue!==" react-mount-point-unstable "))}function $d(){}function Ex(e,t,n,r,i){if(i){if(typeof r=="function"){var s=r;r=function(){var u=Ta(a);s.call(u)}}var a=Tm(t,r,e,0,null,!1,!1,"",$d);return e._reactRootContainer=a,e[Bt]=a.current,Ri(e.nodeType===8?e.parentNode:e),Yn(),a}for(;i=e.lastChild;)e.removeChild(i);if(typeof r=="function"){var o=r;r=function(){var u=Ta(l);o.call(u)}}var l=iu(e,0,!1,null,null,!1,!1,"",$d);return e._reactRootContainer=l,e[Bt]=l.current,Ri(e.nodeType===8?e.parentNode:e),Yn(function(){io(t,l,n,r)}),l}function oo(e,t,n,r,i){var s=n._reactRootContainer;if(s){var a=s;if(typeof i=="function"){var o=i;i=function(){var l=Ta(a);o.call(l)}}io(t,a,e,i)}else a=Ex(n,t,e,i,r);return Ta(a)}op=function(e){switch(e.tag){case 3:var t=e.stateNode;if(t.current.memoizedState.isDehydrated){var n=si(t.pendingLanes);n!==0&&(Nc(t,n|1),Xe(t,ce()),!(H&6)&&(Er=ce()+500,bn()))}break;case 13:Yn(function(){var r=$t(e,1);if(r!==null){var i=Ae();mt(r,e,1,i)}}),su(e,1)}};Cc=function(e){if(e.tag===13){var t=$t(e,134217728);if(t!==null){var n=Ae();mt(t,e,134217728,n)}su(e,134217728)}};lp=function(e){if(e.tag===13){var t=dn(e),n=$t(e,t);if(n!==null){var r=Ae();mt(n,e,t,r)}su(e,t)}};cp=function(){return X};up=function(e,t){var n=X;try{return X=e,t()}finally{X=n}};wl=function(e,t,n){switch(t){case"input":if(ml(e,n),t=n.name,n.type==="radio"&&t!=null){for(n=e;n.parentNode;)n=n.parentNode;for(n=n.querySelectorAll("input[name="+JSON.stringify(""+t)+'][type="radio"]'),t=0;t<n.length;t++){var r=n[t];if(r!==e&&r.form===e.form){var i=Za(r);if(!i)throw Error(M(90));$f(r),ml(r,i)}}}break;case"textarea":Wf(e,n);break;case"select":t=n.value,t!=null&&pr(e,!!n.multiple,t,!1)}};Gf=eu;Zf=Yn;var Tx={usingClientEntryPoint:!1,Events:[rs,or,Za,Kf,Qf,eu]},Zr={findFiberByHostInstance:Pn,bundleType:0,version:"18.3.1",rendererPackageName:"react-dom"},zx={bundleType:Zr.bundleType,version:Zr.version,rendererPackageName:Zr.rendererPackageName,rendererConfig:Zr.rendererConfig,overrideHookState:null,overrideHookStateDeletePath:null,overrideHookStateRenamePath:null,overrideProps:null,overridePropsDeletePath:null,overridePropsRenamePath:null,setErrorHandler:null,setSuspenseHandler:null,scheduleUpdate:null,currentDispatcherRef:Wt.ReactCurrentDispatcher,findHostInstanceByFiber:function(e){return e=ep(e),e===null?null:e.stateNode},findFiberByHostInstance:Zr.findFiberByHostInstance||Px,findHostInstancesForRefresh:null,scheduleRefresh:null,scheduleRoot:null,setRefreshHandler:null,getCurrentFiber:null,reconcilerVersion:"18.3.1-next-f1338f8080-20240426"};if(typeof __REACT_DEVTOOLS_GLOBAL_HOOK__<"u"){var Es=__REACT_DEVTOOLS_GLOBAL_HOOK__;if(!Es.isDisabled&&Es.supportsFiber)try{Xa=Es.inject(zx),St=Es}catch{}}Je.__SECRET_INTERNALS_DO_NOT_USE_OR_YOU_WILL_BE_FIRED=Tx;Je.createPortal=function(e,t){var n=2<arguments.length&&arguments[2]!==void 0?arguments[2]:null;if(!ou(t))throw Error(M(200));return Mx(e,t,null,n)};Je.createRoot=function(e,t){if(!ou(e))throw Error(M(299));var n=!1,r="",i=zm;return t!=null&&(t.unstable_strictMode===!0&&(n=!0),t.identifierPrefix!==void 0&&(r=t.identifierPrefix),t.onRecoverableError!==void 0&&(i=t.onRecoverableError)),t=iu(e,1,!1,null,null,n,!1,r,i),e[Bt]=t.current,Ri(e.nodeType===8?e.parentNode:e),new au(t)};Je.findDOMNode=function(e){if(e==null)return null;if(e.nodeType===1)return e;var t=e._reactInternals;if(t===void 0)throw typeof e.render=="function"?Error(M(188)):(e=Object.keys(e).join(","),Error(M(268,e)));return e=ep(t),e=e===null?null:e.stateNode,e};Je.flushSync=function(e){return Yn(e)};Je.hydrate=function(e,t,n){if(!ao(t))throw Error(M(200));return oo(null,e,t,!0,n)};Je.hydrateRoot=function(e,t,n){if(!ou(e))throw Error(M(405));var r=n!=null&&n.hydratedSources||null,i=!1,s="",a=zm;if(n!=null&&(n.unstable_strictMode===!0&&(i=!0),n.identifierPrefix!==void 0&&(s=n.identifierPrefix),n.onRecoverableError!==void 0&&(a=n.onRecoverableError)),t=Tm(t,null,e,1,n??null,i,!1,s,a),e[Bt]=t.current,Ri(e),r)for(e=0;e<r.length;e++)n=r[e],i=n._getVersion,i=i(n._source),t.mutableSourceEagerHydrationData==null?t.mutableSourceEagerHydrationData=[n,i]:t.mutableSourceEagerHydrationData.push(n,i);return new so(t)};Je.render=function(e,t,n){if(!ao(t))throw Error(M(200));return oo(null,e,t,!1,n)};Je.unmountComponentAtNode=function(e){if(!ao(e))throw Error(M(40));return e._reactRootContainer?(Yn(function(){oo(null,null,e,!1,function(){e._reactRootContainer=null,e[Bt]=null})}),!0):!1};Je.unstable_batchedUpdates=eu;Je.unstable_renderSubtreeIntoContainer=function(e,t,n,r){if(!ao(n))throw Error(M(200));if(e==null||e._reactInternals===void 0)throw Error(M(38));return oo(e,t,n,!1,r)};Je.version="18.3.1-next-f1338f8080-20240426";function Dm(){if(!(typeof __REACT_DEVTOOLS_GLOBAL_HOOK__>"u"||typeof __REACT_DEVTOOLS_GLOBAL_HOOK__.checkDCE!="function"))try{__REACT_DEVTOOLS_GLOBAL_HOOK__.checkDCE(Dm)}catch(e){console.error(e)}}Dm(),Df.exports=Je;var Dx=Df.exports,Hd=Dx;ll.createRoot=Hd.createRoot,ll.hydrateRoot=Hd.hydrateRoot;/**
 * @remix-run/router v1.23.1
 *
 * Copyright (c) Remix Software Inc.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE.md file in the root directory of this source tree.
 *
 * @license MIT
 */function Wi(){return Wi=Object.assign?Object.assign.bind():function(e){for(var t=1;t<arguments.length;t++){var n=arguments[t];for(var r in n)Object.prototype.hasOwnProperty.call(n,r)&&(e[r]=n[r])}return e},Wi.apply(this,arguments)}var Jt;(function(e){e.Pop="POP",e.Push="PUSH",e.Replace="REPLACE"})(Jt||(Jt={}));const Wd="popstate";function Rx(e){e===void 0&&(e={});function t(r,i){let{pathname:s,search:a,hash:o}=r.location;return tc("",{pathname:s,search:a,hash:o},i.state&&i.state.usr||null,i.state&&i.state.key||"default")}function n(r,i){return typeof i=="string"?i:Rm(i)}return Ox(t,n,null,e)}function he(e,t){if(e===!1||e===null||typeof e>"u")throw new Error(t)}function lu(e,t){if(!e){typeof console<"u"&&console.warn(t);try{throw new Error(t)}catch{}}}function Lx(){return Math.random().toString(36).substr(2,8)}function Vd(e,t){return{usr:e.state,key:e.key,idx:t}}function tc(e,t,n,r){return n===void 0&&(n=null),Wi({pathname:typeof e=="string"?e:e.pathname,search:"",hash:""},typeof t=="string"?Ir(t):t,{state:n,key:t&&t.key||r||Lx()})}function Rm(e){let{pathname:t="/",search:n="",hash:r=""}=e;return n&&n!=="?"&&(t+=n.charAt(0)==="?"?n:"?"+n),r&&r!=="#"&&(t+=r.charAt(0)==="#"?r:"#"+r),t}function Ir(e){let t={};if(e){let n=e.indexOf("#");n>=0&&(t.hash=e.substr(n),e=e.substr(0,n));let r=e.indexOf("?");r>=0&&(t.search=e.substr(r),e=e.substr(0,r)),e&&(t.pathname=e)}return t}function Ox(e,t,n,r){r===void 0&&(r={});let{window:i=document.defaultView,v5Compat:s=!1}=r,a=i.history,o=Jt.Pop,l=null,u=d();u==null&&(u=0,a.replaceState(Wi({},a.state,{idx:u}),""));function d(){return(a.state||{idx:null}).idx}function h(){o=Jt.Pop;let y=d(),g=y==null?null:y-u;u=y,l&&l({action:o,location:v.location,delta:g})}function f(y,g){o=Jt.Push;let x=tc(v.location,y,g);u=d()+1;let b=Vd(x,u),k=v.createHref(x);try{a.pushState(b,"",k)}catch(w){if(w instanceof DOMException&&w.name==="DataCloneError")throw w;i.location.assign(k)}s&&l&&l({action:o,location:v.location,delta:1})}function p(y,g){o=Jt.Replace;let x=tc(v.location,y,g);u=d();let b=Vd(x,u),k=v.createHref(x);a.replaceState(b,"",k),s&&l&&l({action:o,location:v.location,delta:0})}function m(y){let g=i.location.origin!=="null"?i.location.origin:i.location.href,x=typeof y=="string"?y:Rm(y);return x=x.replace(/ $/,"%20"),he(g,"No window.location.(origin|href) available to create URL for href: "+x),new URL(x,g)}let v={get action(){return o},get location(){return e(i,a)},listen(y){if(l)throw new Error("A history only accepts one active listener");return i.addEventListener(Wd,h),l=y,()=>{i.removeEventListener(Wd,h),l=null}},createHref(y){return t(i,y)},createURL:m,encodeLocation(y){let g=m(y);return{pathname:g.pathname,search:g.search,hash:g.hash}},push:f,replace:p,go(y){return a.go(y)}};return v}var Ud;(function(e){e.data="data",e.deferred="deferred",e.redirect="redirect",e.error="error"})(Ud||(Ud={}));function Ax(e,t,n){return n===void 0&&(n="/"),Ix(e,t,n)}function Ix(e,t,n,r){let i=typeof t=="string"?Ir(t):t,s=Am(i.pathname||"/",n);if(s==null)return null;let a=Lm(e);Fx(a);let o=null;for(let l=0;o==null&&l<a.length;++l){let u=Zx(s);o=Kx(a[l],u)}return o}function Lm(e,t,n,r){t===void 0&&(t=[]),n===void 0&&(n=[]),r===void 0&&(r="");let i=(s,a,o)=>{let l={relativePath:o===void 0?s.path||"":o,caseSensitive:s.caseSensitive===!0,childrenIndex:a,route:s};l.relativePath.startsWith("/")&&(he(l.relativePath.startsWith(r),'Absolute route path "'+l.relativePath+'" nested under path '+('"'+r+'" is not valid. An absolute child route path ')+"must start with the combined path of all its parent routes."),l.relativePath=l.relativePath.slice(r.length));let u=An([r,l.relativePath]),d=n.concat(l);s.children&&s.children.length>0&&(he(s.index!==!0,"Index routes must not have child routes. Please remove "+('all child routes from route path "'+u+'".')),Lm(s.children,t,d,u)),!(s.path==null&&!s.index)&&t.push({path:u,score:Yx(u,s.index),routesMeta:d})};return e.forEach((s,a)=>{var o;if(s.path===""||!((o=s.path)!=null&&o.includes("?")))i(s,a);else for(let l of Om(s.path))i(s,a,l)}),t}function Om(e){let t=e.split("/");if(t.length===0)return[];let[n,...r]=t,i=n.endsWith("?"),s=n.replace(/\?$/,"");if(r.length===0)return i?[s,""]:[s];let a=Om(r.join("/")),o=[];return o.push(...a.map(l=>l===""?s:[s,l].join("/"))),i&&o.push(...a),o.map(l=>e.startsWith("/")&&l===""?"/":l)}function Fx(e){e.sort((t,n)=>t.score!==n.score?n.score-t.score:Xx(t.routesMeta.map(r=>r.childrenIndex),n.routesMeta.map(r=>r.childrenIndex)))}const Bx=/^:[\w-]+$/,$x=3,Hx=2,Wx=1,Vx=10,Ux=-2,Yd=e=>e==="*";function Yx(e,t){let n=e.split("/"),r=n.length;return n.some(Yd)&&(r+=Ux),t&&(r+=Hx),n.filter(i=>!Yd(i)).reduce((i,s)=>i+(Bx.test(s)?$x:s===""?Wx:Vx),r)}function Xx(e,t){return e.length===t.length&&e.slice(0,-1).every((r,i)=>r===t[i])?e[e.length-1]-t[t.length-1]:0}function Kx(e,t,n){let{routesMeta:r}=e,i={},s="/",a=[];for(let o=0;o<r.length;++o){let l=r[o],u=o===r.length-1,d=s==="/"?t:t.slice(s.length)||"/",h=Qx({path:l.relativePath,caseSensitive:l.caseSensitive,end:u},d),f=l.route;if(!h)return null;Object.assign(i,h.params),a.push({params:i,pathname:An([s,h.pathname]),pathnameBase:n0(An([s,h.pathnameBase])),route:f}),h.pathnameBase!=="/"&&(s=An([s,h.pathnameBase]))}return a}function Qx(e,t){typeof e=="string"&&(e={path:e,caseSensitive:!1,end:!0});let[n,r]=Gx(e.path,e.caseSensitive,e.end),i=t.match(n);if(!i)return null;let s=i[0],a=s.replace(/(.)\/+$/,"$1"),o=i.slice(1);return{params:r.reduce((u,d,h)=>{let{paramName:f,isOptional:p}=d;if(f==="*"){let v=o[h]||"";a=s.slice(0,s.length-v.length).replace(/(.)\/+$/,"$1")}const m=o[h];return p&&!m?u[f]=void 0:u[f]=(m||"").replace(/%2F/g,"/"),u},{}),pathname:s,pathnameBase:a,pattern:e}}function Gx(e,t,n){t===void 0&&(t=!1),n===void 0&&(n=!0),lu(e==="*"||!e.endsWith("*")||e.endsWith("/*"),'Route path "'+e+'" will be treated as if it were '+('"'+e.replace(/\*$/,"/*")+'" because the `*` character must ')+"always follow a `/` in the pattern. To get rid of this warning, "+('please change the route path to "'+e.replace(/\*$/,"/*")+'".'));let r=[],i="^"+e.replace(/\/*\*?$/,"").replace(/^\/*/,"/").replace(/[\\.*+^${}|()[\]]/g,"\\$&").replace(/\/:([\w-]+)(\?)?/g,(a,o,l)=>(r.push({paramName:o,isOptional:l!=null}),l?"/?([^\\/]+)?":"/([^\\/]+)"));return e.endsWith("*")?(r.push({paramName:"*"}),i+=e==="*"||e==="/*"?"(.*)$":"(?:\\/(.+)|\\/*)$"):n?i+="\\/*$":e!==""&&e!=="/"&&(i+="(?:(?=\\/|$))"),[new RegExp(i,t?void 0:"i"),r]}function Zx(e){try{return e.split("/").map(t=>decodeURIComponent(t).replace(/\//g,"%2F")).join("/")}catch(t){return lu(!1,'The URL path "'+e+'" could not be decoded because it is is a malformed URL segment. This is probably due to a bad percent '+("encoding ("+t+").")),e}}function Am(e,t){if(t==="/")return e;if(!e.toLowerCase().startsWith(t.toLowerCase()))return null;let n=t.endsWith("/")?t.length-1:t.length,r=e.charAt(n);return r&&r!=="/"?null:e.slice(n)||"/"}const qx=/^(?:[a-z][a-z0-9+.-]*:|\/\/)/i,Jx=e=>qx.test(e);function e0(e,t){t===void 0&&(t="/");let{pathname:n,search:r="",hash:i=""}=typeof e=="string"?Ir(e):e,s;if(n)if(Jx(n))s=n;else{if(n.includes("//")){let a=n;n=n.replace(/\/\/+/g,"/"),lu(!1,"Pathnames cannot have embedded double slashes - normalizing "+(a+" -> "+n))}n.startsWith("/")?s=Xd(n.substring(1),"/"):s=Xd(n,t)}else s=t;return{pathname:s,search:r0(r),hash:i0(i)}}function Xd(e,t){let n=t.replace(/\/+$/,"").split("/");return e.split("/").forEach(i=>{i===".."?n.length>1&&n.pop():i!=="."&&n.push(i)}),n.length>1?n.join("/"):"/"}function Vo(e,t,n,r){return"Cannot include a '"+e+"' character in a manually specified "+("`to."+t+"` field ["+JSON.stringify(r)+"].  Please separate it out to the ")+("`to."+n+"` field. Alternatively you may provide the full path as ")+'a string in <Link to="..."> and the router will parse it for you.'}function t0(e){return e.filter((t,n)=>n===0||t.route.path&&t.route.path.length>0)}function Im(e,t){let n=t0(e);return t?n.map((r,i)=>i===n.length-1?r.pathname:r.pathnameBase):n.map(r=>r.pathnameBase)}function Fm(e,t,n,r){r===void 0&&(r=!1);let i;typeof e=="string"?i=Ir(e):(i=Wi({},e),he(!i.pathname||!i.pathname.includes("?"),Vo("?","pathname","search",i)),he(!i.pathname||!i.pathname.includes("#"),Vo("#","pathname","hash",i)),he(!i.search||!i.search.includes("#"),Vo("#","search","hash",i)));let s=e===""||i.pathname==="",a=s?"/":i.pathname,o;if(a==null)o=n;else{let h=t.length-1;if(!r&&a.startsWith("..")){let f=a.split("/");for(;f[0]==="..";)f.shift(),h-=1;i.pathname=f.join("/")}o=h>=0?t[h]:"/"}let l=e0(i,o),u=a&&a!=="/"&&a.endsWith("/"),d=(s||a===".")&&n.endsWith("/");return!l.pathname.endsWith("/")&&(u||d)&&(l.pathname+="/"),l}const An=e=>e.join("/").replace(/\/\/+/g,"/"),n0=e=>e.replace(/\/+$/,"").replace(/^\/*/,"/"),r0=e=>!e||e==="?"?"":e.startsWith("?")?e:"?"+e,i0=e=>!e||e==="#"?"":e.startsWith("#")?e:"#"+e;function s0(e){return e!=null&&typeof e.status=="number"&&typeof e.statusText=="string"&&typeof e.internal=="boolean"&&"data"in e}const Bm=["post","put","patch","delete"];new Set(Bm);const a0=["get",...Bm];new Set(a0);/**
 * React Router v6.30.2
 *
 * Copyright (c) Remix Software Inc.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE.md file in the root directory of this source tree.
 *
 * @license MIT
 */function Vi(){return Vi=Object.assign?Object.assign.bind():function(e){for(var t=1;t<arguments.length;t++){var n=arguments[t];for(var r in n)Object.prototype.hasOwnProperty.call(n,r)&&(e[r]=n[r])}return e},Vi.apply(this,arguments)}const cu=_.createContext(null),o0=_.createContext(null),ss=_.createContext(null),lo=_.createContext(null),kn=_.createContext({outlet:null,matches:[],isDataRoute:!1}),$m=_.createContext(null);function as(){return _.useContext(lo)!=null}function co(){return as()||he(!1),_.useContext(lo).location}function Hm(e){_.useContext(ss).static||_.useLayoutEffect(e)}function uu(){let{isDataRoute:e}=_.useContext(kn);return e?k0():l0()}function l0(){as()||he(!1);let e=_.useContext(cu),{basename:t,future:n,navigator:r}=_.useContext(ss),{matches:i}=_.useContext(kn),{pathname:s}=co(),a=JSON.stringify(Im(i,n.v7_relativeSplatPath)),o=_.useRef(!1);return Hm(()=>{o.current=!0}),_.useCallback(function(u,d){if(d===void 0&&(d={}),!o.current)return;if(typeof u=="number"){r.go(u);return}let h=Fm(u,JSON.parse(a),s,d.relative==="path");e==null&&t!=="/"&&(h.pathname=h.pathname==="/"?t:An([t,h.pathname])),(d.replace?r.replace:r.push)(h,d.state,d)},[t,r,a,s,e])}function c0(){let{matches:e}=_.useContext(kn),t=e[e.length-1];return t?t.params:{}}function u0(e,t){return d0(e,t)}function d0(e,t,n,r){as()||he(!1);let{navigator:i}=_.useContext(ss),{matches:s}=_.useContext(kn),a=s[s.length-1],o=a?a.params:{};a&&a.pathname;let l=a?a.pathnameBase:"/";a&&a.route;let u=co(),d;if(t){var h;let y=typeof t=="string"?Ir(t):t;l==="/"||(h=y.pathname)!=null&&h.startsWith(l)||he(!1),d=y}else d=u;let f=d.pathname||"/",p=f;if(l!=="/"){let y=l.replace(/^\//,"").split("/");p="/"+f.replace(/^\//,"").split("/").slice(y.length).join("/")}let m=Ax(e,{pathname:p}),v=g0(m&&m.map(y=>Object.assign({},y,{params:Object.assign({},o,y.params),pathname:An([l,i.encodeLocation?i.encodeLocation(y.pathname).pathname:y.pathname]),pathnameBase:y.pathnameBase==="/"?l:An([l,i.encodeLocation?i.encodeLocation(y.pathnameBase).pathname:y.pathnameBase])})),s,n,r);return t&&v?_.createElement(lo.Provider,{value:{location:Vi({pathname:"/",search:"",hash:"",state:null,key:"default"},d),navigationType:Jt.Pop}},v):v}function h0(){let e=b0(),t=s0(e)?e.status+" "+e.statusText:e instanceof Error?e.message:JSON.stringify(e),n=e instanceof Error?e.stack:null,i={padding:"0.5rem",backgroundColor:"rgba(200,200,200, 0.5)"};return _.createElement(_.Fragment,null,_.createElement("h2",null,"Unexpected Application Error!"),_.createElement("h3",{style:{fontStyle:"italic"}},t),n?_.createElement("pre",{style:i},n):null,null)}const f0=_.createElement(h0,null);class p0 extends _.Component{constructor(t){super(t),this.state={location:t.location,revalidation:t.revalidation,error:t.error}}static getDerivedStateFromError(t){return{error:t}}static getDerivedStateFromProps(t,n){return n.location!==t.location||n.revalidation!=="idle"&&t.revalidation==="idle"?{error:t.error,location:t.location,revalidation:t.revalidation}:{error:t.error!==void 0?t.error:n.error,location:n.location,revalidation:t.revalidation||n.revalidation}}componentDidCatch(t,n){console.error("React Router caught the following error during render",t,n)}render(){return this.state.error!==void 0?_.createElement(kn.Provider,{value:this.props.routeContext},_.createElement($m.Provider,{value:this.state.error,children:this.props.component})):this.props.children}}function m0(e){let{routeContext:t,match:n,children:r}=e,i=_.useContext(cu);return i&&i.static&&i.staticContext&&(n.route.errorElement||n.route.ErrorBoundary)&&(i.staticContext._deepestRenderedBoundaryId=n.route.id),_.createElement(kn.Provider,{value:t},r)}function g0(e,t,n,r){var i;if(t===void 0&&(t=[]),n===void 0&&(n=null),r===void 0&&(r=null),e==null){var s;if(!n)return null;if(n.errors)e=n.matches;else if((s=r)!=null&&s.v7_partialHydration&&t.length===0&&!n.initialized&&n.matches.length>0)e=n.matches;else return null}let a=e,o=(i=n)==null?void 0:i.errors;if(o!=null){let d=a.findIndex(h=>h.route.id&&(o==null?void 0:o[h.route.id])!==void 0);d>=0||he(!1),a=a.slice(0,Math.min(a.length,d+1))}let l=!1,u=-1;if(n&&r&&r.v7_partialHydration)for(let d=0;d<a.length;d++){let h=a[d];if((h.route.HydrateFallback||h.route.hydrateFallbackElement)&&(u=d),h.route.id){let{loaderData:f,errors:p}=n,m=h.route.loader&&f[h.route.id]===void 0&&(!p||p[h.route.id]===void 0);if(h.route.lazy||m){l=!0,u>=0?a=a.slice(0,u+1):a=[a[0]];break}}}return a.reduceRight((d,h,f)=>{let p,m=!1,v=null,y=null;n&&(p=o&&h.route.id?o[h.route.id]:void 0,v=h.route.errorElement||f0,l&&(u<0&&f===0?(w0("route-fallback"),m=!0,y=null):u===f&&(m=!0,y=h.route.hydrateFallbackElement||null)));let g=t.concat(a.slice(0,f+1)),x=()=>{let b;return p?b=v:m?b=y:h.route.Component?b=_.createElement(h.route.Component,null):h.route.element?b=h.route.element:b=d,_.createElement(m0,{match:h,routeContext:{outlet:d,matches:g,isDataRoute:n!=null},children:b})};return n&&(h.route.ErrorBoundary||h.route.errorElement||f===0)?_.createElement(p0,{location:n.location,revalidation:n.revalidation,component:v,error:p,children:x(),routeContext:{outlet:null,matches:g,isDataRoute:!0}}):x()},null)}var Wm=function(e){return e.UseBlocker="useBlocker",e.UseRevalidator="useRevalidator",e.UseNavigateStable="useNavigate",e}(Wm||{}),Vm=function(e){return e.UseBlocker="useBlocker",e.UseLoaderData="useLoaderData",e.UseActionData="useActionData",e.UseRouteError="useRouteError",e.UseNavigation="useNavigation",e.UseRouteLoaderData="useRouteLoaderData",e.UseMatches="useMatches",e.UseRevalidator="useRevalidator",e.UseNavigateStable="useNavigate",e.UseRouteId="useRouteId",e}(Vm||{});function v0(e){let t=_.useContext(cu);return t||he(!1),t}function y0(e){let t=_.useContext(o0);return t||he(!1),t}function x0(e){let t=_.useContext(kn);return t||he(!1),t}function Um(e){let t=x0(),n=t.matches[t.matches.length-1];return n.route.id||he(!1),n.route.id}function b0(){var e;let t=_.useContext($m),n=y0(),r=Um();return t!==void 0?t:(e=n.errors)==null?void 0:e[r]}function k0(){let{router:e}=v0(Wm.UseNavigateStable),t=Um(Vm.UseNavigateStable),n=_.useRef(!1);return Hm(()=>{n.current=!0}),_.useCallback(function(i,s){s===void 0&&(s={}),n.current&&(typeof i=="number"?e.navigate(i):e.navigate(i,Vi({fromRouteId:t},s)))},[e,t])}const Kd={};function w0(e,t,n){Kd[e]||(Kd[e]=!0)}function _0(e,t){e==null||e.v7_startTransition,e==null||e.v7_relativeSplatPath}function j0(e){let{to:t,replace:n,state:r,relative:i}=e;as()||he(!1);let{future:s,static:a}=_.useContext(ss),{matches:o}=_.useContext(kn),{pathname:l}=co(),u=uu(),d=Fm(t,Im(o,s.v7_relativeSplatPath),l,i==="path"),h=JSON.stringify(d);return _.useEffect(()=>u(JSON.parse(h),{replace:n,state:r,relative:i}),[u,h,i,n,r]),null}function Yt(e){he(!1)}function S0(e){let{basename:t="/",children:n=null,location:r,navigationType:i=Jt.Pop,navigator:s,static:a=!1,future:o}=e;as()&&he(!1);let l=t.replace(/^\/*/,"/"),u=_.useMemo(()=>({basename:l,navigator:s,static:a,future:Vi({v7_relativeSplatPath:!1},o)}),[l,o,s,a]);typeof r=="string"&&(r=Ir(r));let{pathname:d="/",search:h="",hash:f="",state:p=null,key:m="default"}=r,v=_.useMemo(()=>{let y=Am(d,l);return y==null?null:{location:{pathname:y,search:h,hash:f,state:p,key:m},navigationType:i}},[l,d,h,f,p,m,i]);return v==null?null:_.createElement(ss.Provider,{value:u},_.createElement(lo.Provider,{children:n,value:v}))}function N0(e){let{children:t,location:n}=e;return u0(nc(t),n)}new Promise(()=>{});function nc(e,t){t===void 0&&(t=[]);let n=[];return _.Children.forEach(e,(r,i)=>{if(!_.isValidElement(r))return;let s=[...t,i];if(r.type===_.Fragment){n.push.apply(n,nc(r.props.children,s));return}r.type!==Yt&&he(!1),!r.props.index||!r.props.children||he(!1);let a={id:r.props.id||s.join("-"),caseSensitive:r.props.caseSensitive,element:r.props.element,Component:r.props.Component,index:r.props.index,path:r.props.path,loader:r.props.loader,action:r.props.action,errorElement:r.props.errorElement,ErrorBoundary:r.props.ErrorBoundary,hasErrorBoundary:r.props.ErrorBoundary!=null||r.props.errorElement!=null,shouldRevalidate:r.props.shouldRevalidate,handle:r.props.handle,lazy:r.props.lazy};r.props.children&&(a.children=nc(r.props.children,s)),n.push(a)}),n}/**
 * React Router DOM v6.30.2
 *
 * Copyright (c) Remix Software Inc.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE.md file in the root directory of this source tree.
 *
 * @license MIT
 */const C0="6";try{window.__reactRouterVersion=C0}catch{}const M0="startTransition",Qd=wv[M0];function P0(e){let{basename:t,children:n,future:r,window:i}=e,s=_.useRef();s.current==null&&(s.current=Rx({window:i,v5Compat:!0}));let a=s.current,[o,l]=_.useState({action:a.action,location:a.location}),{v7_startTransition:u}=r||{},d=_.useCallback(h=>{u&&Qd?Qd(()=>l(h)):l(h)},[l,u]);return _.useLayoutEffect(()=>a.listen(d),[a,d]),_.useEffect(()=>_0(r),[r]),_.createElement(S0,{basename:t,children:n,location:o.location,navigationType:o.action,navigator:a,future:r})}var Gd;(function(e){e.UseScrollRestoration="useScrollRestoration",e.UseSubmit="useSubmit",e.UseSubmitFetcher="useSubmitFetcher",e.UseFetcher="useFetcher",e.useViewTransitionState="useViewTransitionState"})(Gd||(Gd={}));var Zd;(function(e){e.UseFetcher="useFetcher",e.UseFetchers="useFetchers",e.UseScrollRestoration="useScrollRestoration"})(Zd||(Zd={}));const na=new Map;function E0(e,t={}){const{initialData:n=null,onSuccess:r,onError:i,cacheKey:s,cacheDuration:a=3e4}=t,[o,l]=_.useState({data:n,loading:!1,error:null}),u=_.useRef(!0);_.useEffect(()=>()=>{u.current=!1},[]);const d=_.useCallback(async()=>{if(s){const p=na.get(s);if(p&&Date.now()-p.timestamp<a)return l({data:p.data,loading:!1,error:null}),p.data}l(p=>({...p,loading:!0,error:null}));try{const p=await e();return u.current&&(l({data:p,loading:!1,error:null}),s&&na.set(s,{data:p,timestamp:Date.now()}),r==null||r(p)),p}catch(p){const m=p instanceof Error?p:new Error(String(p));throw u.current&&(l(v=>({...v,loading:!1,error:m})),i==null||i(m)),m}},[e,s,a,r,i]),h=_.useCallback(()=>{l({data:n,loading:!1,error:null}),s&&na.delete(s)},[n,s]),f=_.useCallback(p=>{l(m=>({...m,data:typeof p=="function"?p(m.data):p}))},[]);return{...o,execute:d,reset:h,setData:f,refetch:d}}function Zn(e,t={}){const n=E0(e,t),r=_.useRef(!1);return _.useEffect(()=>{r.current||(r.current=!0,n.execute().catch(()=>{}))},[]),n}function oi(e,t={}){const[n,r]=_.useState({data:null,loading:!1,error:null}),i=_.useRef(!0);_.useEffect(()=>()=>{i.current=!1},[]);const s=_.useCallback(async o=>{var l,u;r(d=>({...d,loading:!0,error:null}));try{const d=await e(o);return i.current&&(r({data:d,loading:!1,error:null}),(l=t.onSuccess)==null||l.call(t,d)),d}catch(d){const h=d instanceof Error?d:new Error(String(d));throw i.current&&(r(f=>({...f,loading:!1,error:h})),(u=t.onError)==null||u.call(t,h)),h}},[e,t]),a=_.useCallback(()=>{r({data:null,loading:!1,error:null})},[]);return{...n,mutate:s,reset:a}}function T0(e){na.delete(e)}const z0="/api";async function V(e,t){const n=await fetch(`${z0}${e}`,{headers:{"Content-Type":"application/json",...t==null?void 0:t.headers},...t});if(!n.ok){const r=await n.json().catch(()=>({detail:n.statusText}));throw new Error(r.detail||`HTTP ${n.status}`)}return n.json()}const D0={getOverview:()=>V("/dashboard/overview"),getDomains:()=>V("/dashboard/domains"),getDomainDetail:e=>V(`/dashboard/domains/${e}`),getSpecialists:e=>{const t=new URLSearchParams;e!=null&&e.domain&&t.set("domain",e.domain),(e==null?void 0:e.active_only)!==void 0&&t.set("active_only",String(e.active_only)),e!=null&&e.limit&&t.set("limit",String(e.limit));const n=t.toString();return V(`/dashboard/specialists${n?`?${n}`:""}`)},getSpecialistDetail:e=>V(`/dashboard/specialists/${e}`),getBudget:()=>V("/dashboard/budget"),getStats:()=>V("/dashboard/stats")},R0={getMode:()=>V("/evaluation/mode"),setMode:e=>V("/evaluation/mode",{method:"POST",body:JSON.stringify({mode:e})}),getStats:()=>V("/evaluation/stats"),getScoringCommitteeStats:()=>V("/evaluation/scoring-committee/stats"),getAICouncilStats:()=>V("/evaluation/ai-council/stats"),getComparisonStats:()=>V("/evaluation/comparison-stats"),resetStats:()=>V("/evaluation/reset-stats",{method:"POST"})},L0={getStatus:()=>V("/benchmark/status"),discover:()=>V("/benchmark/discover"),list:e=>{const t=e?`?domain=${e}`:"";return V(`/benchmark/list${t}`)},run:e=>V("/benchmark/run",{method:"POST",body:JSON.stringify(e||{})}),pause:()=>V("/benchmark/pause",{method:"POST"}),resume:()=>V("/benchmark/resume",{method:"POST"}),cancel:()=>V("/benchmark/cancel",{method:"POST"}),getHistory:e=>{const t=new URLSearchParams;e!=null&&e.limit&&t.set("limit",String(e.limit)),e!=null&&e.domain&&t.set("domain",e.domain);const n=t.toString();return V(`/benchmark/history${n?`?${n}`:""}`)},getRunDetail:e=>V(`/benchmark/history/${e}`),getStats:()=>V("/benchmark/stats")},O0={getRecent:e=>{const t=new URLSearchParams;e!=null&&e.limit&&t.set("limit",String(e.limit)),e!=null&&e.domain&&t.set("domain",e.domain),e!=null&&e.specialist_id&&t.set("specialist_id",e.specialist_id);const n=t.toString();return V(`/tasks/recent${n?`?${n}`:""}`)},getTaskDetail:e=>V(`/tasks/${e}`),submitFeedback:(e,t)=>V(`/tasks/${e}/feedback`,{method:"POST",body:JSON.stringify(t)}),getPendingFeedback:e=>{const t=e?`?limit=${e}`:"";return V(`/tasks/pending-feedback${t}`)},getFeedbackStats:()=>V("/tasks/feedback/stats"),getBySpecialist:(e,t)=>{const n=t?`?limit=${t}`:"";return V(`/tasks/by-specialist/${e}${n}`)},getByDomain:(e,t)=>{const n=t?`?limit=${t}`:"";return V(`/tasks/by-domain/${e}${n}`)}},A0={check:()=>fetch("/health").then(e=>e.json()),getVersion:()=>fetch("/version").then(e=>e.json())},Ve={dashboard:D0,evaluation:R0,benchmark:L0,tasks:O0,health:A0};function I0(){return Zn(()=>Ve.dashboard.getOverview(),{cacheKey:"dashboard:overview",cacheDuration:1e4})}function F0(){return Zn(()=>Ve.dashboard.getDomains(),{cacheKey:"dashboard:domains",cacheDuration:3e4})}function B0(){return Zn(()=>Ve.dashboard.getBudget(),{cacheKey:"dashboard:budget",cacheDuration:1e4})}function $0(e){const t=`tasks:recent:${JSON.stringify(e||{})}`;return Zn(()=>Ve.tasks.getRecent(e),{cacheKey:t,cacheDuration:15e3})}function H0(){var n,r,i;const e=Zn(()=>Ve.evaluation.getMode(),{cacheKey:"evaluation:mode",cacheDuration:3e4}),t=oi(s=>Ve.evaluation.setMode(s),{onSuccess:()=>{T0("evaluation:mode"),e.refetch()}});return{mode:((n=e.data)==null?void 0:n.mode)||"both",scoringCommitteeEnabled:((r=e.data)==null?void 0:r.scoring_committee_enabled)??!0,aiCouncilEnabled:((i=e.data)==null?void 0:i.ai_council_enabled)??!0,loading:e.loading||t.loading,error:e.error||t.error,setMode:t.mutate,refetch:e.refetch}}function W0(){return Zn(()=>Ve.benchmark.getStatus(),{cacheKey:"benchmark:status",cacheDuration:5e3})}function V0(){const e=oi(i=>Ve.benchmark.run(i)),t=oi(()=>Ve.benchmark.pause()),n=oi(()=>Ve.benchmark.resume()),r=oi(()=>Ve.benchmark.cancel());return{run:e.mutate,pause:t.mutate,resume:n.mutate,cancel:r.mutate,loading:e.loading||t.loading||n.loading||r.loading,error:e.error||t.error||n.error||r.error}}function U0(){return Zn(()=>Ve.health.check(),{cacheKey:"health:check",cacheDuration:1e4})}function Y0(){const e=I0(),t=F0(),n=B0(),r=$0({limit:10}),i=H0(),s=W0(),a=U0(),o=_.useMemo(()=>e.loading||t.loading||n.loading||r.loading||a.loading,[e.loading,t.loading,n.loading,r.loading,a.loading]),l=_.useMemo(()=>e.error||t.error||n.error||r.error||a.error,[e.error,t.error,n.error,r.error,a.error]),u=_.useCallback(()=>{e.refetch(),t.refetch(),n.refetch(),r.refetch(),i.refetch(),s.refetch(),a.refetch()},[e,t,n,r,i,s,a]);return{overview:e.data,domains:t.data,budget:n.data,recentTasks:r.data,evaluationMode:i.mode,benchmarkStatus:s.data,health:a.data,loading:o,error:l,refetchAll:u,setEvaluationMode:i.setMode}}function X0(e={}){const{interval:t=3e4,enabled:n=!0,onRefresh:r,immediate:i=!1}=e,[s,a]=_.useState(null),[o,l]=_.useState(!1),u=_.useRef(null),d=_.useRef(r);_.useEffect(()=>{d.current=r},[r]);const h=_.useCallback(async()=>{var v;if(!o){l(!0);try{await((v=d.current)==null?void 0:v.call(d)),a(new Date)}finally{l(!1)}}},[o]),f=_.useCallback(()=>{u.current&&clearTimeout(u.current),n&&t>0&&(u.current=setTimeout(()=>{h().then(f)},t))},[n,t,h]);_.useEffect(()=>(n&&(i?h().then(f):f()),()=>{u.current&&clearTimeout(u.current)}),[n,f,i,h]);const p=_.useCallback(()=>{u.current&&(clearTimeout(u.current),u.current=null)},[]),m=_.useCallback(()=>{f()},[f]);return{lastRefresh:s,isRefreshing:o,refresh:h,pause:p,resume:m,enabled:n}}let K0=0;function Q0(e={}){const{maxNotifications:t=5,defaultDuration:n=5e3}=e,[r,i]=_.useState([]),s=_.useRef(new Map),a=_.useCallback(p=>{const m=s.current.get(p);m&&(clearTimeout(m),s.current.delete(p)),i(v=>v.filter(y=>y.id!==p))},[]),o=_.useCallback(p=>{const m=`notification-${++K0}`,v={...p,id:m,dismissible:p.dismissible??!0,duration:p.duration??n};if(i(y=>{const g=[v,...y];return g.length>t?(g.slice(t).forEach(b=>{const k=s.current.get(b.id);k&&(clearTimeout(k),s.current.delete(b.id))}),g.slice(0,t)):g}),v.duration&&v.duration>0){const y=setTimeout(()=>{a(m)},v.duration);s.current.set(m,y)}return m},[a,t,n]),l=_.useCallback((p,m)=>o({type:"info",title:p,message:m}),[o]),u=_.useCallback((p,m)=>o({type:"success",title:p,message:m}),[o]),d=_.useCallback((p,m)=>o({type:"warning",title:p,message:m}),[o]),h=_.useCallback((p,m)=>o({type:"error",title:p,message:m,duration:8e3}),[o]),f=_.useCallback(()=>{s.current.forEach(p=>clearTimeout(p)),s.current.clear(),i([])},[]);return{notifications:r,add:o,dismiss:a,info:l,success:u,warning:d,error:h,clearAll:f}}const Ym=_.createContext(null);function G0({children:e}){const t=Q0();return c.jsx(Ym.Provider,{value:t,children:e})}function Z0(){return _.useContext(Ym)}/**
 * @license lucide-react v0.303.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */var q0={xmlns:"http://www.w3.org/2000/svg",width:24,height:24,viewBox:"0 0 24 24",fill:"none",stroke:"currentColor",strokeWidth:2,strokeLinecap:"round",strokeLinejoin:"round"};/**
 * @license lucide-react v0.303.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const J0=e=>e.replace(/([a-z0-9])([A-Z])/g,"$1-$2").toLowerCase().trim(),O=(e,t)=>{const n=_.forwardRef(({color:r="currentColor",size:i=24,strokeWidth:s=2,absoluteStrokeWidth:a,className:o="",children:l,...u},d)=>_.createElement("svg",{ref:d,...q0,width:i,height:i,stroke:r,strokeWidth:a?Number(s)*24/Number(i):s,className:["lucide",`lucide-${J0(e)}`,o].join(" "),...u},[...t.map(([h,f])=>_.createElement(h,f)),...Array.isArray(l)?l:[l]]));return n.displayName=`${e}`,n};/**
 * @license lucide-react v0.303.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const za=O("Activity",[["path",{d:"M22 12h-4l-3 9L9 3l-3 9H2",key:"d5dnw9"}]]);/**
 * @license lucide-react v0.303.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Xm=O("AlertCircle",[["circle",{cx:"12",cy:"12",r:"10",key:"1mglay"}],["line",{x1:"12",x2:"12",y1:"8",y2:"12",key:"1pkeuh"}],["line",{x1:"12",x2:"12.01",y1:"16",y2:"16",key:"4dfq90"}]]);/**
 * @license lucide-react v0.303.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const rc=O("AlertTriangle",[["path",{d:"m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z",key:"c3ski4"}],["path",{d:"M12 9v4",key:"juzpu7"}],["path",{d:"M12 17h.01",key:"p32p05"}]]);/**
 * @license lucide-react v0.303.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const qd=O("ArrowLeft",[["path",{d:"m12 19-7-7 7-7",key:"1l729n"}],["path",{d:"M19 12H5",key:"x3x0zl"}]]);/**
 * @license lucide-react v0.303.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const du=O("Bell",[["path",{d:"M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9",key:"1qo2s2"}],["path",{d:"M10.3 21a1.94 1.94 0 0 0 3.4 0",key:"qgo35s"}]]);/**
 * @license lucide-react v0.303.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Tr=O("Brain",[["path",{d:"M9.5 2A2.5 2.5 0 0 1 12 4.5v15a2.5 2.5 0 0 1-4.96.44 2.5 2.5 0 0 1-2.96-3.08 3 3 0 0 1-.34-5.58 2.5 2.5 0 0 1 1.32-4.24 2.5 2.5 0 0 1 1.98-3A2.5 2.5 0 0 1 9.5 2Z",key:"1mhkh5"}],["path",{d:"M14.5 2A2.5 2.5 0 0 0 12 4.5v15a2.5 2.5 0 0 0 4.96.44 2.5 2.5 0 0 0 2.96-3.08 3 3 0 0 0 .34-5.58 2.5 2.5 0 0 0-1.32-4.24 2.5 2.5 0 0 0-1.98-3A2.5 2.5 0 0 0 14.5 2Z",key:"1d6s00"}]]);/**
 * @license lucide-react v0.303.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const os=O("Calendar",[["rect",{width:"18",height:"18",x:"3",y:"4",rx:"2",ry:"2",key:"eu3xkr"}],["line",{x1:"16",x2:"16",y1:"2",y2:"6",key:"m3sa8f"}],["line",{x1:"8",x2:"8",y1:"2",y2:"6",key:"18kwsl"}],["line",{x1:"3",x2:"21",y1:"10",y2:"10",key:"xt86sb"}]]);/**
 * @license lucide-react v0.303.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const hu=O("CheckCircle",[["path",{d:"M22 11.08V12a10 10 0 1 1-5.93-9.14",key:"g774vq"}],["path",{d:"m9 11 3 3L22 4",key:"1pflzl"}]]);/**
 * @license lucide-react v0.303.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Km=O("Check",[["path",{d:"M20 6 9 17l-5-5",key:"1gmf2c"}]]);/**
 * @license lucide-react v0.303.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Qm=O("ChevronDown",[["path",{d:"m6 9 6 6 6-6",key:"qrunsl"}]]);/**
 * @license lucide-react v0.303.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const gn=O("Clock",[["circle",{cx:"12",cy:"12",r:"10",key:"1mglay"}],["polyline",{points:"12 6 12 12 16 14",key:"68esgv"}]]);/**
 * @license lucide-react v0.303.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Gm=O("Code",[["polyline",{points:"16 18 22 12 16 6",key:"z7tu5w"}],["polyline",{points:"8 6 2 12 8 18",key:"1eg1df"}]]);/**
 * @license lucide-react v0.303.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const br=O("DollarSign",[["line",{x1:"12",x2:"12",y1:"2",y2:"22",key:"7eqyqh"}],["path",{d:"M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6",key:"1b0p4s"}]]);/**
 * @license lucide-react v0.303.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const e1=O("Download",[["path",{d:"M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4",key:"ih7n3h"}],["polyline",{points:"7 10 12 15 17 10",key:"2ggqvy"}],["line",{x1:"12",x2:"12",y1:"15",y2:"3",key:"1vk2je"}]]);/**
 * @license lucide-react v0.303.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const t1=O("Eye",[["path",{d:"M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z",key:"rwhkz3"}],["circle",{cx:"12",cy:"12",r:"3",key:"1v7zrd"}]]);/**
 * @license lucide-react v0.303.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Zm=O("FileCode",[["path",{d:"M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z",key:"1nnpy2"}],["polyline",{points:"14 2 14 8 20 8",key:"1ew0cm"}],["path",{d:"m10 13-2 2 2 2",key:"17smn8"}],["path",{d:"m14 17 2-2-2-2",key:"14mezr"}]]);/**
 * @license lucide-react v0.303.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const qm=O("FileText",[["path",{d:"M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z",key:"1nnpy2"}],["polyline",{points:"14 2 14 8 20 8",key:"1ew0cm"}],["line",{x1:"16",x2:"8",y1:"13",y2:"13",key:"14keom"}],["line",{x1:"16",x2:"8",y1:"17",y2:"17",key:"17nazh"}],["line",{x1:"10",x2:"8",y1:"9",y2:"9",key:"1a5vjj"}]]);/**
 * @license lucide-react v0.303.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Uo=O("Filter",[["polygon",{points:"22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3",key:"1yg77f"}]]);/**
 * @license lucide-react v0.303.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const n1=O("GitCompare",[["circle",{cx:"18",cy:"18",r:"3",key:"1xkwt0"}],["circle",{cx:"6",cy:"6",r:"3",key:"1lh9wr"}],["path",{d:"M13 6h3a2 2 0 0 1 2 2v7",key:"1yeb86"}],["path",{d:"M11 18H8a2 2 0 0 1-2-2V9",key:"19pyzm"}]]);/**
 * @license lucide-react v0.303.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const r1=O("LayoutDashboard",[["rect",{width:"7",height:"9",x:"3",y:"3",rx:"1",key:"10lvy0"}],["rect",{width:"7",height:"5",x:"14",y:"3",rx:"1",key:"16une8"}],["rect",{width:"7",height:"9",x:"14",y:"12",rx:"1",key:"1hutg5"}],["rect",{width:"7",height:"5",x:"3",y:"16",rx:"1",key:"ldoo1y"}]]);/**
 * @license lucide-react v0.303.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const i1=O("MessageSquare",[["path",{d:"M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z",key:"1lielz"}]]);/**
 * @license lucide-react v0.303.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Ui=O("Minus",[["path",{d:"M5 12h14",key:"1ays0h"}]]);/**
 * @license lucide-react v0.303.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Jm=O("Moon",[["path",{d:"M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z",key:"a7tn18"}]]);/**
 * @license lucide-react v0.303.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const s1=O("MoreHorizontal",[["circle",{cx:"12",cy:"12",r:"1",key:"41hilf"}],["circle",{cx:"19",cy:"12",r:"1",key:"1wjl8i"}],["circle",{cx:"5",cy:"12",r:"1",key:"1pcz8c"}]]);/**
 * @license lucide-react v0.303.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const a1=O("Pause",[["rect",{width:"4",height:"16",x:"6",y:"4",key:"iffhe4"}],["rect",{width:"4",height:"16",x:"14",y:"4",key:"sjin7j"}]]);/**
 * @license lucide-react v0.303.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const eg=O("Play",[["polygon",{points:"5 3 19 12 5 21 5 3",key:"191637"}]]);/**
 * @license lucide-react v0.303.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const o1=O("Plus",[["path",{d:"M5 12h14",key:"1ays0h"}],["path",{d:"M12 5v14",key:"s699le"}]]);/**
 * @license lucide-react v0.303.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Yi=O("RefreshCw",[["path",{d:"M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8",key:"v9h5vc"}],["path",{d:"M21 3v5h-5",key:"1q7to0"}],["path",{d:"M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16",key:"3uifl3"}],["path",{d:"M8 16H3v5",key:"1cv678"}]]);/**
 * @license lucide-react v0.303.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Fr=O("RotateCcw",[["path",{d:"M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8",key:"1357e3"}],["path",{d:"M3 3v5h5",key:"1xhq8a"}]]);/**
 * @license lucide-react v0.303.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const tg=O("Save",[["path",{d:"M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z",key:"1owoqh"}],["polyline",{points:"17 21 17 13 7 13 7 21",key:"1md35c"}],["polyline",{points:"7 3 7 8 15 8",key:"8nz8an"}]]);/**
 * @license lucide-react v0.303.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const l1=O("Scale",[["path",{d:"m16 16 3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1Z",key:"7g6ntu"}],["path",{d:"m2 16 3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1Z",key:"ijws7r"}],["path",{d:"M7 21h10",key:"1b0cd5"}],["path",{d:"M12 3v18",key:"108xh3"}],["path",{d:"M3 7h2c2 0 5-1 7-2 2 1 5 2 7 2h2",key:"3gwbw2"}]]);/**
 * @license lucide-react v0.303.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const ng=O("Search",[["circle",{cx:"11",cy:"11",r:"8",key:"4ej97u"}],["path",{d:"m21 21-4.3-4.3",key:"1qie3q"}]]);/**
 * @license lucide-react v0.303.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const rg=O("Send",[["path",{d:"m22 2-7 20-4-9-9-4Z",key:"1q3vgg"}],["path",{d:"M22 2 11 13",key:"nzbqef"}]]);/**
 * @license lucide-react v0.303.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const ig=O("Settings",[["path",{d:"M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z",key:"1qme2f"}],["circle",{cx:"12",cy:"12",r:"3",key:"1v7zrd"}]]);/**
 * @license lucide-react v0.303.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const c1=O("Shield",[["path",{d:"M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10",key:"1irkt0"}]]);/**
 * @license lucide-react v0.303.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const kr=O("Skull",[["circle",{cx:"9",cy:"12",r:"1",key:"1vctgf"}],["circle",{cx:"15",cy:"12",r:"1",key:"1tmaij"}],["path",{d:"M8 20v2h8v-2",key:"ded4og"}],["path",{d:"m12.5 17-.5-1-.5 1h1z",key:"3me087"}],["path",{d:"M16 20a2 2 0 0 0 1.56-3.25 8 8 0 1 0-11.12 0A2 2 0 0 0 8 20",key:"xq9p5u"}]]);/**
 * @license lucide-react v0.303.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const u1=O("Target",[["circle",{cx:"12",cy:"12",r:"10",key:"1mglay"}],["circle",{cx:"12",cy:"12",r:"6",key:"1vlfrh"}],["circle",{cx:"12",cy:"12",r:"2",key:"1c9p78"}]]);/**
 * @license lucide-react v0.303.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const fu=O("Terminal",[["polyline",{points:"4 17 10 11 4 5",key:"akl6gq"}],["line",{x1:"12",x2:"20",y1:"19",y2:"19",key:"q2wloq"}]]);/**
 * @license lucide-react v0.303.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const sg=O("ThumbsDown",[["path",{d:"M17 14V2",key:"8ymqnk"}],["path",{d:"M9 18.12 10 14H4.17a2 2 0 0 1-1.92-2.56l2.33-8A2 2 0 0 1 6.5 2H20a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2h-2.76a2 2 0 0 0-1.79 1.11L12 22h0a3.13 3.13 0 0 1-3-3.88Z",key:"s6e0r"}]]);/**
 * @license lucide-react v0.303.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const ag=O("ThumbsUp",[["path",{d:"M7 10v12",key:"1qc93n"}],["path",{d:"M15 5.88 14 10h5.83a2 2 0 0 1 1.92 2.56l-2.33 8A2 2 0 0 1 17.5 22H4a2 2 0 0 1-2-2v-8a2 2 0 0 1 2-2h2.76a2 2 0 0 0 1.79-1.11L12 2h0a3.13 3.13 0 0 1 3 3.88Z",key:"y3tblf"}]]);/**
 * @license lucide-react v0.303.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const d1=O("Timer",[["line",{x1:"10",x2:"14",y1:"2",y2:"2",key:"14vaq8"}],["line",{x1:"12",x2:"15",y1:"14",y2:"11",key:"17fdiu"}],["circle",{cx:"12",cy:"14",r:"8",key:"1e1u0o"}]]);/**
 * @license lucide-react v0.303.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const ls=O("Trash2",[["path",{d:"M3 6h18",key:"d0wm0j"}],["path",{d:"M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6",key:"4alrt4"}],["path",{d:"M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2",key:"v07s0e"}],["line",{x1:"10",x2:"10",y1:"11",y2:"17",key:"1uufr5"}],["line",{x1:"14",x2:"14",y1:"11",y2:"17",key:"xtxkd"}]]);/**
 * @license lucide-react v0.303.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Br=O("TrendingDown",[["polyline",{points:"22 17 13.5 8.5 8.5 13.5 2 7",key:"1r2t7k"}],["polyline",{points:"16 17 22 17 22 11",key:"11uiuu"}]]);/**
 * @license lucide-react v0.303.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Xn=O("TrendingUp",[["polyline",{points:"22 7 13.5 15.5 8.5 10.5 2 17",key:"126l90"}],["polyline",{points:"16 7 22 7 22 13",key:"kwv8wd"}]]);/**
 * @license lucide-react v0.303.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const h1=O("User",[["path",{d:"M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2",key:"975kel"}],["circle",{cx:"12",cy:"7",r:"4",key:"17ys0d"}]]);/**
 * @license lucide-react v0.303.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const ic=O("Users",[["path",{d:"M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2",key:"1yyitq"}],["circle",{cx:"9",cy:"7",r:"4",key:"nufk8"}],["path",{d:"M22 21v-2a4 4 0 0 0-3-3.87",key:"kshegd"}],["path",{d:"M16 3.13a4 4 0 0 1 0 7.75",key:"1da9ce"}]]);/**
 * @license lucide-react v0.303.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Da=O("Wallet",[["path",{d:"M21 12V7H5a2 2 0 0 1 0-4h14v4",key:"195gfw"}],["path",{d:"M3 5v14a2 2 0 0 0 2 2h16v-5",key:"195n9w"}],["path",{d:"M18 12a2 2 0 0 0 0 4h4v-4Z",key:"vllfpd"}]]);/**
 * @license lucide-react v0.303.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const pu=O("XCircle",[["circle",{cx:"12",cy:"12",r:"10",key:"1mglay"}],["path",{d:"m15 9-6 6",key:"1uzhvr"}],["path",{d:"m9 9 6 6",key:"z0biqf"}]]);/**
 * @license lucide-react v0.303.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const f1=O("X",[["path",{d:"M18 6 6 18",key:"1bl5f8"}],["path",{d:"m6 6 12 12",key:"d8bk6v"}]]);/**
 * @license lucide-react v0.303.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Xi=O("Zap",[["polygon",{points:"13 2 3 14 12 14 11 22 21 10 12 10 13 2",key:"45s27k"}]]),ge=({variant:e="secondary",size:t="md",icon:n,iconPosition:r="left",loading:i=!1,fullWidth:s=!1,disabled:a,className:o="",children:l,...u})=>{const d="btn",h=`btn-${e}`,f=t!=="md"?`btn-${t}`:"",p=s?"w-full":"",m=!l&&n?"btn-icon":"";return c.jsx("button",{className:`${d} ${h} ${f} ${p} ${m} ${o}`.trim(),disabled:a||i,...u,children:i?c.jsxs(c.Fragment,{children:[c.jsx("span",{className:"animate-spin",children:c.jsxs("svg",{className:"icon",viewBox:"0 0 24 24",fill:"none",stroke:"currentColor",strokeWidth:"2",children:[c.jsx("circle",{cx:"12",cy:"12",r:"10",strokeOpacity:"0.25"}),c.jsx("path",{d:"M12 2a10 10 0 0 1 10 10"})]})}),l&&c.jsx("span",{children:"Loading..."})]}):c.jsxs(c.Fragment,{children:[n&&r==="left"&&c.jsx(n,{className:t==="sm"?"icon-sm":"icon"}),l,n&&r==="right"&&c.jsx(n,{className:t==="sm"?"icon-sm":"icon"})]})})},mu=_.forwardRef(({label:e,error:t,icon:n,fullWidth:r=!0,className:i="",...s},a)=>{const o=`input ${t?"input-error":""} ${n?"pl-10":""} ${i}`.trim();return c.jsxs("div",{className:r?"w-full":"",children:[e&&c.jsx("label",{className:"block text-sm text-secondary mb-2 font-medium",children:e}),c.jsxs("div",{className:"relative",children:[n&&c.jsx(n,{className:"absolute left-3 top-1/2 -translate-y-1/2 icon text-tertiary pointer-events-none"}),c.jsx("input",{ref:a,className:o,...s})]}),t&&c.jsx("p",{className:"text-xs text-danger mt-1",children:t})]})});mu.displayName="Input";const p1=_.forwardRef(({label:e,error:t,fullWidth:n=!0,className:r="",...i},s)=>{const a=`input textarea ${t?"input-error":""} ${r}`.trim();return c.jsxs("div",{className:n?"w-full":"",children:[e&&c.jsx("label",{className:"block text-sm text-secondary mb-2 font-medium",children:e}),c.jsx("textarea",{ref:s,className:a,...i}),t&&c.jsx("p",{className:"text-xs text-danger mt-1",children:t})]})});p1.displayName="Textarea";const m1=_.forwardRef(({label:e,error:t,options:n,fullWidth:r=!0,className:i="",...s},a)=>{const o=`input select ${t?"input-error":""} ${i}`.trim();return c.jsxs("div",{className:r?"w-full":"",children:[e&&c.jsx("label",{className:"block text-sm text-secondary mb-2 font-medium",children:e}),c.jsx("select",{ref:a,className:o,...s,children:n.map(l=>c.jsx("option",{value:l.value,children:l.label},l.value))}),t&&c.jsx("p",{className:"text-xs text-danger mt-1",children:t})]})});m1.displayName="Select";const cs=({children:e,variant:t="neutral",size:n="md",dot:r=!1,className:i=""})=>{const s=n==="sm"?"badge-sm":"",a=r?"badge-dot":"";return c.jsx("span",{className:`badge badge-${t} ${s} ${a} ${i}`.trim(),children:e})},gu=({status:e,size:t="md"})=>{const n={active:"Active",idle:"Idle",running:"Running",completed:"Completed",failed:"Failed",pending:"Pending",probation:"Probation"};return c.jsx(cs,{variant:e,size:t,dot:!0,children:n[e]||e})},$r=({isOpen:e,onClose:t,title:n,size:r="md",children:i,footer:s,closeOnOverlayClick:a=!0,closeOnEscape:o=!0})=>{const l=_.useCallback(d=>{d.key==="Escape"&&o&&t()},[o,t]);_.useEffect(()=>(e&&(document.addEventListener("keydown",l),document.body.style.overflow="hidden"),()=>{document.removeEventListener("keydown",l),document.body.style.overflow=""}),[e,l]);const u=d=>{d.target===d.currentTarget&&a&&t()};return c.jsx("div",{className:`modal-overlay ${e?"active":""}`,onClick:u,role:"dialog","aria-modal":"true","aria-hidden":!e,children:c.jsxs("div",{className:`modal modal-${r}`,children:[n&&c.jsxs("div",{className:"modal-header",children:[c.jsx("div",{className:"modal-title",children:n}),c.jsx("button",{className:"modal-close",onClick:t,"aria-label":"Close",children:c.jsx(f1,{className:"icon"})})]}),c.jsx("div",{className:"modal-body",children:i}),s&&c.jsx("div",{className:"modal-footer",children:s})]})})},us=({value:e,max:t=100,size:n="md",variant:r="primary",showLabel:i=!1,label:s,className:a=""})=>{const o=Math.min(Math.max(e/t*100,0),100),l=n!=="md"?`progress-bar-${n}`:"";return c.jsxs("div",{className:a,children:[(i||s)&&c.jsxs("div",{className:"flex justify-between text-sm mb-1",children:[c.jsx("span",{className:"text-secondary",children:s}),c.jsxs("span",{className:"text-primary font-medium",children:[o.toFixed(0),"%"]})]}),c.jsx("div",{className:`progress-bar ${l}`,children:c.jsx("div",{className:`progress-bar-fill ${r!=="primary"?r:""}`,style:{width:`${o}%`}})})]})},zn=({options:e,value:t,onChange:n,placeholder:r="Select...",disabled:i=!1,className:s=""})=>{const[a,o]=_.useState(!1),l=_.useRef(null),u=e.find(h=>h.value===t);_.useEffect(()=>{const h=f=>{l.current&&!l.current.contains(f.target)&&o(!1)};return document.addEventListener("mousedown",h),()=>document.removeEventListener("mousedown",h)},[]);const d=h=>{n==null||n(h),o(!1)};return c.jsxs("div",{ref:l,className:`dropdown ${a?"open":""} ${s}`,children:[c.jsxs("button",{type:"button",className:"dropdown-trigger",onClick:()=>!i&&o(!a),disabled:i,"aria-haspopup":"listbox","aria-expanded":a,children:[u?c.jsxs(c.Fragment,{children:[u.icon,c.jsx("span",{className:"flex-1 text-left",children:u.label})]}):c.jsx("span",{className:"flex-1 text-left text-tertiary",children:r}),c.jsx(Qm,{className:`icon transition ${a?"rotate-180":""}`})]}),c.jsx("div",{className:"dropdown-content",role:"listbox",children:e.map(h=>c.jsxs("div",{className:`dropdown-item ${h.value===t?"active":""}`,onClick:()=>d(h.value),role:"option","aria-selected":h.value===t,children:[h.icon,c.jsx("span",{className:"flex-1",children:h.label}),h.value===t&&c.jsx(Km,{className:"icon-sm"})]},h.value))})]})},In=({systemHealth:e="healthy",onSettingsClick:t,onNotificationsClick:n,onBudgetClick:r})=>{const i=()=>{switch(e){case"healthy":return"var(--accent-primary)";case"degraded":return"var(--accent-warning)";case"unhealthy":return"var(--accent-danger)";default:return"var(--text-tertiary)"}};return c.jsxs("header",{className:"header",children:[c.jsxs("div",{className:"header-logo",children:[c.jsx("div",{className:"logo-icon",children:c.jsxs("svg",{width:"24",height:"24",viewBox:"0 0 24 24",fill:"none",children:[c.jsx("circle",{cx:"12",cy:"12",r:"10",stroke:"var(--accent-primary)",strokeWidth:"2"}),c.jsx("circle",{cx:"12",cy:"12",r:"4",fill:"var(--accent-primary)"}),c.jsx("path",{d:"M12 2v4M12 18v4M2 12h4M18 12h4",stroke:"var(--accent-primary)",strokeWidth:"2"})]})}),c.jsx("span",{className:"logo-text",children:"JARVIS"}),c.jsx("span",{className:"logo-version",children:"v7.5"})]}),c.jsxs("div",{className:"header-status",children:[c.jsx(za,{className:"icon-sm",style:{color:i()}}),c.jsxs("span",{className:"status-label",style:{color:i()},children:["System ",e.charAt(0).toUpperCase()+e.slice(1)]})]}),c.jsxs("div",{className:"header-actions",children:[c.jsx(ge,{variant:"ghost",size:"sm",icon:Da,onClick:r,"aria-label":"Budget"}),c.jsx(ge,{variant:"ghost",size:"sm",icon:du,onClick:n,"aria-label":"Notifications"}),c.jsx(ge,{variant:"ghost",size:"sm",icon:ig,onClick:t,"aria-label":"Settings"})]}),c.jsx("style",{children:`
        .header {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          height: var(--header-height);
          background: var(--bg-secondary);
          border-bottom: 1px solid var(--border-primary);
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 0 var(--space-4);
          z-index: var(--z-sticky);
        }

        .header-logo {
          display: flex;
          align-items: center;
          gap: var(--space-2);
        }

        .logo-icon {
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .logo-text {
          font-family: var(--font-display);
          font-size: var(--text-xl);
          font-weight: var(--weight-bold);
          color: var(--accent-primary);
          letter-spacing: 2px;
        }

        .logo-version {
          font-size: var(--text-xs);
          color: var(--text-tertiary);
          padding: 2px 6px;
          background: var(--bg-tertiary);
          border-radius: var(--radius-sm);
        }

        .header-status {
          display: flex;
          align-items: center;
          gap: var(--space-2);
          padding: var(--space-1) var(--space-3);
          background: var(--bg-tertiary);
          border-radius: var(--radius-full);
        }

        .status-label {
          font-size: var(--text-xs);
          font-weight: var(--weight-medium);
        }

        .header-actions {
          display: flex;
          align-items: center;
          gap: var(--space-1);
        }

        @media (max-width: 768px) {
          .header-status .status-label {
            display: none;
          }
        }
      `})]})},g1=[{id:"administration",name:"Administration",icon:fu,specialistCount:3,avgScore:.87},{id:"code_generation",name:"Code Generation",icon:Gm,specialistCount:2,avgScore:.78},{id:"business_documents",name:"Business Docs",icon:qm,specialistCount:1,avgScore:.82}],Fn=({activePage:e,domains:t=g1,onNavigate:n,onDomainClick:r,onRunBenchmark:i,onForceEvolution:s,onNewTask:a,onViewGraveyard:o})=>{const l=uu(),u=co(),d=e||(u.pathname==="/"?"dashboard":u.pathname.slice(1)),h=m=>m>=.85?"var(--accent-primary)":m>=.7?"var(--accent-secondary)":m>=.5?"var(--accent-warning)":"var(--accent-danger)",f=m=>{l("/"),n==null||n(m)},p=()=>{o&&o()};return c.jsxs("aside",{className:"sidebar",children:[c.jsxs("nav",{className:"sidebar-nav",children:[c.jsxs("div",{className:"nav-section",children:[c.jsx("div",{className:"nav-section-title",children:"Navigation"}),c.jsxs("button",{className:`nav-item ${d==="dashboard"?"active":""}`,onClick:()=>f("dashboard"),children:[c.jsx(r1,{className:"icon"}),c.jsx("span",{children:"Dashboard"})]})]}),c.jsxs("div",{className:"nav-section",children:[c.jsx("div",{className:"nav-section-title",children:"Domains"}),t.map(m=>c.jsxs("button",{className:"nav-item domain-item",onClick:()=>r==null?void 0:r(m.id),children:[c.jsx(m.icon,{className:"icon"}),c.jsx("span",{className:"domain-name",children:m.name}),c.jsx("span",{className:"domain-score",style:{color:h(m.avgScore)},children:(m.avgScore||0).toFixed(2)})]},m.id))]}),c.jsxs("div",{className:"nav-section",children:[c.jsx("div",{className:"nav-section-title",children:"Quick Actions"}),c.jsx(ge,{variant:"ghost",size:"sm",icon:eg,onClick:i,fullWidth:!0,className:"justify-start",children:"Run Benchmark"}),c.jsx(ge,{variant:"ghost",size:"sm",icon:Xi,onClick:s,fullWidth:!0,className:"justify-start",children:"Force Evolution"}),c.jsx(ge,{variant:"ghost",size:"sm",icon:o1,onClick:a,fullWidth:!0,className:"justify-start",children:"New Task"}),c.jsx(ge,{variant:"ghost",size:"sm",icon:kr,onClick:p,fullWidth:!0,className:"justify-start",children:"Graveyard"})]})]}),c.jsx("style",{children:`
        .sidebar {
          position: fixed;
          top: var(--header-height);
          left: 0;
          bottom: 0;
          width: var(--sidebar-width);
          background: var(--bg-secondary);
          border-right: 1px solid var(--border-primary);
          overflow-y: auto;
          z-index: var(--z-sticky);
        }

        .sidebar-nav {
          padding: var(--space-4);
        }

        .nav-section {
          margin-bottom: var(--space-6);
        }

        .nav-section-title {
          font-size: var(--text-xs);
          font-weight: var(--weight-semibold);
          color: var(--text-tertiary);
          text-transform: uppercase;
          letter-spacing: 0.5px;
          margin-bottom: var(--space-2);
          padding: 0 var(--space-2);
        }

        .nav-item {
          display: flex;
          align-items: center;
          gap: var(--space-2);
          width: 100%;
          padding: var(--space-2);
          border: none;
          background: transparent;
          color: var(--text-secondary);
          font-family: var(--font-mono);
          font-size: var(--text-sm);
          border-radius: var(--radius-md);
          cursor: pointer;
          transition: all var(--transition-fast);
          text-align: left;
        }

        .nav-item:hover {
          background: var(--bg-hover);
          color: var(--text-primary);
        }

        .nav-item.active {
          background: var(--accent-primary-dim);
          color: var(--accent-primary);
        }

        .domain-item {
          justify-content: flex-start;
        }

        .domain-name {
          flex: 1;
        }

        .domain-score {
          font-weight: var(--weight-semibold);
          font-size: var(--text-xs);
        }

        @media (max-width: 1024px) {
          .sidebar {
            transform: translateX(-100%);
            transition: transform var(--transition-normal);
          }

          .sidebar.open {
            transform: translateX(0);
          }
        }
      `})]})},Bn=({children:e,className:t=""})=>c.jsxs("main",{className:`main-content ${t}`,children:[e,c.jsx("style",{children:`
        .main-content {
          margin-top: var(--header-height);
          margin-left: var(--sidebar-width);
          padding: var(--space-6);
          min-height: calc(100vh - var(--header-height));
          background: var(--bg-primary);
        }

        @media (max-width: 1024px) {
          .main-content {
            margin-left: 0;
          }
        }
      `})]}),ds=({title:e,subtitle:t,actions:n})=>c.jsxs("div",{className:"content-header",children:[c.jsxs("div",{children:[c.jsx("h1",{className:"content-title",children:e}),t&&c.jsx("p",{className:"content-subtitle",children:t})]}),n&&c.jsx("div",{className:"content-actions",children:n}),c.jsx("style",{children:`
        .content-header {
          display: flex;
          align-items: flex-start;
          justify-content: space-between;
          margin-bottom: var(--space-6);
        }

        .content-title {
          display: flex;
          align-items: center;
          gap: var(--space-3);
          font-size: var(--text-2xl);
          font-weight: var(--weight-semibold);
          color: var(--text-primary);
        }

        .content-subtitle {
          font-size: var(--text-sm);
          color: var(--text-secondary);
          margin-top: var(--space-1);
        }

        .content-actions {
          display: flex;
          align-items: center;
          gap: var(--space-2);
        }
      `})]}),le=({title:e,children:t,className:n=""})=>c.jsxs("section",{className:`content-section ${n}`,children:[e&&c.jsx("h2",{className:"section-title",children:e}),t,c.jsx("style",{children:`
        .content-section {
          margin-bottom: var(--space-6);
        }

        .section-title {
          font-size: var(--text-lg);
          font-weight: var(--weight-semibold);
          color: var(--text-primary);
          margin-bottom: var(--space-4);
        }
      `})]}),v1=({mode:e,onChange:t,disabled:n=!1})=>{const r=[{value:"scoring_committee",label:"Scoring Committee",icon:c.jsx(l1,{className:"icon-md"}),description:"Multi-checker evaluation"},{value:"ai_council",label:"AI Council",icon:c.jsx(ic,{className:"icon-md"}),description:"Bootstrap consensus voting"},{value:"both",label:"Both (Compare)",icon:c.jsx(n1,{className:"icon-md"}),description:"Run both and compare"}];return c.jsxs("div",{className:"evaluation-selector",children:[c.jsx("div",{className:"evaluation-selector-label",children:"Evaluation Mode"}),c.jsx("div",{className:"evaluation-selector-options",children:r.map(i=>c.jsxs("button",{className:`evaluation-option ${e===i.value?"active":""}`,onClick:()=>t(i.value),disabled:n,children:[c.jsx("div",{className:"evaluation-option-icon",children:i.icon}),c.jsxs("div",{className:"evaluation-option-info",children:[c.jsx("div",{className:"evaluation-option-label",children:i.label}),c.jsx("div",{className:"evaluation-option-desc",children:i.description})]})]},i.value))}),c.jsx("style",{children:`
        .evaluation-selector {
          background: var(--bg-secondary);
          border: 1px solid var(--border-primary);
          border-radius: var(--radius-lg);
          padding: var(--space-4);
        }

        .evaluation-selector-label {
          font-size: var(--text-sm);
          font-weight: var(--weight-semibold);
          color: var(--text-secondary);
          margin-bottom: var(--space-3);
          text-transform: uppercase;
          letter-spacing: 0.5px;
        }

        .evaluation-selector-options {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: var(--space-2);
        }

        .evaluation-option {
          display: flex;
          align-items: center;
          gap: var(--space-3);
          padding: var(--space-3);
          background: var(--bg-primary);
          border: 1px solid var(--border-primary);
          border-radius: var(--radius-md);
          cursor: pointer;
          transition: all var(--transition-fast);
          text-align: left;
        }

        .evaluation-option:hover:not(:disabled) {
          border-color: var(--accent-primary);
        }

        .evaluation-option.active {
          background: var(--accent-primary-dim);
          border-color: var(--accent-primary);
        }

        .evaluation-option:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .evaluation-option-icon {
          color: var(--text-tertiary);
        }

        .evaluation-option.active .evaluation-option-icon {
          color: var(--accent-primary);
        }

        .evaluation-option-info {
          flex: 1;
        }

        .evaluation-option-label {
          font-size: var(--text-sm);
          font-weight: var(--weight-medium);
          color: var(--text-primary);
        }

        .evaluation-option.active .evaluation-option-label {
          color: var(--accent-primary);
        }

        .evaluation-option-desc {
          font-size: var(--text-xs);
          color: var(--text-tertiary);
          margin-top: 2px;
        }

        @media (max-width: 768px) {
          .evaluation-selector-options {
            grid-template-columns: 1fr;
          }
        }
      `})]})},og=({specialist:e,onClick:t,onDelete:n,showActions:r=!1})=>{const i=()=>e.trend?e.trend>0?c.jsx(Xn,{className:"icon-xs trend-up"}):e.trend<0?c.jsx(Br,{className:"icon-xs trend-down"}):c.jsx(Ui,{className:"icon-xs"}):c.jsx(Ui,{className:"icon-xs"}),s=a=>a>=.85?"var(--accent-primary)":a>=.7?"var(--accent-secondary)":a>=.5?"var(--accent-warning)":"var(--accent-danger)";return c.jsxs("div",{className:`specialist-row ${t?"clickable":""}`,onClick:t,role:t?"button":void 0,tabIndex:t?0:void 0,onKeyDown:a=>a.key==="Enter"&&(t==null?void 0:t()),children:[c.jsx("div",{className:"specialist-icon",children:c.jsx(Tr,{className:"icon"})}),c.jsxs("div",{className:"specialist-info",children:[c.jsx("div",{className:"specialist-name",children:e.name}),c.jsxs("div",{className:"specialist-meta",children:[c.jsxs("span",{className:"specialist-id",children:["#",e.id.slice(0,8)]}),e.generation!==void 0&&c.jsxs(c.Fragment,{children:[c.jsx("span",{className:"separator",children:"•"}),c.jsxs("span",{children:["Gen ",e.generation]})]})]})]}),c.jsx("div",{className:"specialist-status",children:c.jsx(gu,{status:e.status,size:"sm"})}),c.jsxs("div",{className:"specialist-score",children:[c.jsx("span",{className:"score-value",style:{color:s(e.score)},children:(e.score||0).toFixed(3)}),c.jsx("span",{className:"score-trend",children:i()})]}),e.tasks_completed!==void 0&&c.jsxs("div",{className:"specialist-tasks",children:[c.jsx("span",{className:"tasks-count",children:e.tasks_completed}),c.jsx("span",{className:"tasks-label",children:"tasks"})]}),r&&n&&c.jsx("button",{className:"specialist-delete",onClick:a=>{a.stopPropagation(),n()},"aria-label":"Delete specialist",children:c.jsx(ls,{className:"icon-sm"})}),c.jsx("style",{children:`
        .specialist-row {
          display: flex;
          align-items: center;
          gap: var(--space-3);
          padding: var(--space-3);
          background: var(--bg-tertiary);
          border-radius: var(--radius-md);
          transition: all var(--transition-fast);
        }

        .specialist-row.clickable {
          cursor: pointer;
        }

        .specialist-row.clickable:hover {
          background: var(--bg-hover);
        }

        .specialist-icon {
          width: 32px;
          height: 32px;
          display: flex;
          align-items: center;
          justify-content: center;
          background: var(--bg-secondary);
          border-radius: var(--radius-sm);
          color: var(--text-secondary);
          flex-shrink: 0;
        }

        .specialist-info {
          flex: 1;
          min-width: 0;
        }

        .specialist-name {
          font-size: var(--text-sm);
          font-weight: var(--weight-medium);
          color: var(--text-primary);
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }

        .specialist-meta {
          font-size: var(--text-xs);
          color: var(--text-tertiary);
          display: flex;
          gap: var(--space-1);
        }

        .specialist-id {
          font-family: var(--font-mono);
        }

        .separator {
          color: var(--border-primary);
        }

        .specialist-status {
          flex-shrink: 0;
        }

        .specialist-score {
          display: flex;
          align-items: center;
          gap: var(--space-1);
          flex-shrink: 0;
        }

        .score-value {
          font-family: var(--font-mono);
          font-size: var(--text-sm);
          font-weight: var(--weight-bold);
        }

        .score-trend {
          display: flex;
          align-items: center;
        }

        .trend-up {
          color: var(--accent-primary);
        }

        .trend-down {
          color: var(--accent-danger);
        }

        .specialist-tasks {
          display: flex;
          flex-direction: column;
          align-items: center;
          flex-shrink: 0;
          min-width: 40px;
        }

        .tasks-count {
          font-size: var(--text-sm);
          font-weight: var(--weight-semibold);
          color: var(--text-primary);
        }

        .tasks-label {
          font-size: var(--text-xs);
          color: var(--text-tertiary);
        }

        .specialist-delete {
          padding: var(--space-1);
          background: transparent;
          border: none;
          color: var(--text-tertiary);
          cursor: pointer;
          border-radius: var(--radius-sm);
          transition: all var(--transition-fast);
          flex-shrink: 0;
        }

        .specialist-delete:hover {
          background: var(--accent-danger-dim);
          color: var(--accent-danger);
        }
      `})]})},y1={administration:fu,code_generation:Gm,business_documents:qm},x1=({domain:e,specialists:t=[],onSpecialistClick:n,onClick:r,loading:i=!1})=>{const[s,a]=_.useState(!1),o=y1[e.name.toLowerCase().replace(/\s+/g,"_")]||fu,l=u=>u>=.85?"var(--accent-primary)":u>=.7?"var(--accent-secondary)":u>=.5?"var(--accent-warning)":"var(--accent-danger)";return c.jsxs("div",{className:`domain-card ${s?"expanded":""}`,children:[c.jsxs("div",{className:"domain-card-header",onClick:()=>a(!s),role:"button",tabIndex:0,onKeyDown:u=>u.key==="Enter"&&a(!s),children:[c.jsx("div",{className:"domain-card-icon",children:c.jsx(o,{className:"icon-lg"})}),c.jsxs("div",{className:"domain-card-info",children:[c.jsx("div",{className:"domain-card-name",children:e.name}),c.jsxs("div",{className:"domain-card-meta",children:[c.jsxs("span",{children:[e.specialists," specialists"]}),c.jsx("span",{className:"separator",children:"|"}),c.jsxs("span",{children:["Avg: ",(e.avg_score||0).toFixed(2)]})]})]}),c.jsxs("div",{className:"domain-card-stats",children:[c.jsxs("div",{className:"domain-stat",children:[c.jsx("div",{className:"domain-stat-value",children:e.tasks_today}),c.jsx("div",{className:"domain-stat-label",children:"Tasks"})]}),c.jsxs("div",{className:"domain-stat",children:[c.jsx("div",{className:"domain-stat-value",style:{color:l(e.best_score)},children:(e.best_score||0).toFixed(2)}),c.jsx("div",{className:"domain-stat-label",children:"Best"})]})]}),c.jsx("div",{className:`domain-card-expand ${s?"rotated":""}`,children:c.jsx(Qm,{className:"icon"})})]}),e.evolution_paused&&c.jsx("div",{className:"domain-card-warning",children:c.jsx(cs,{variant:"warning",size:"sm",dot:!0,children:"Evolution Paused"})}),s&&c.jsxs("div",{className:"domain-card-body",children:[c.jsxs("div",{className:"domain-convergence",children:[c.jsx("div",{className:"convergence-label",children:"Convergence Progress"}),c.jsx(us,{value:e.convergence_progress*100,size:"sm",variant:e.convergence_progress>=.9?"primary":"warning"})]}),c.jsx("div",{className:"specialist-list",children:i?c.jsx("div",{className:"skeleton skeleton-card",style:{height:"60px"}}):t.length>0?t.map(u=>c.jsx(og,{specialist:u,onClick:()=>n==null?void 0:n(u)},u.id)):c.jsx("div",{className:"empty-specialists",children:"No specialists in this domain"})})]}),c.jsx("style",{children:`
        .domain-card {
          background: var(--bg-secondary);
          border: 1px solid var(--border-primary);
          border-radius: var(--radius-lg);
          overflow: hidden;
          transition: all var(--transition-fast);
        }

        .domain-card:hover {
          border-color: var(--border-secondary);
        }

        .domain-card.expanded {
          border-color: var(--accent-primary);
        }

        .domain-card-header {
          display: flex;
          align-items: center;
          gap: var(--space-3);
          padding: var(--space-4);
          cursor: pointer;
        }

        .domain-card-icon {
          width: 40px;
          height: 40px;
          display: flex;
          align-items: center;
          justify-content: center;
          background: var(--accent-primary-dim);
          color: var(--accent-primary);
          border-radius: var(--radius-md);
          flex-shrink: 0;
        }

        .domain-card-info {
          flex: 1;
          min-width: 0;
        }

        .domain-card-name {
          font-size: var(--text-md);
          font-weight: var(--weight-semibold);
          color: var(--text-primary);
        }

        .domain-card-meta {
          font-size: var(--text-xs);
          color: var(--text-tertiary);
          display: flex;
          gap: var(--space-2);
        }

        .separator {
          color: var(--border-primary);
        }

        .domain-card-stats {
          display: flex;
          gap: var(--space-4);
        }

        .domain-stat {
          text-align: center;
        }

        .domain-stat-value {
          font-size: var(--text-lg);
          font-weight: var(--weight-bold);
          color: var(--text-primary);
        }

        .domain-stat-label {
          font-size: var(--text-xs);
          color: var(--text-tertiary);
        }

        .domain-card-expand {
          color: var(--text-tertiary);
          transition: transform var(--transition-fast);
        }

        .domain-card-expand.rotated {
          transform: rotate(180deg);
        }

        .domain-card-warning {
          padding: 0 var(--space-4) var(--space-3);
        }

        .domain-card-body {
          padding: 0 var(--space-4) var(--space-4);
          border-top: 1px solid var(--border-primary);
        }

        .domain-convergence {
          padding: var(--space-3) 0;
        }

        .convergence-label {
          font-size: var(--text-xs);
          color: var(--text-tertiary);
          margin-bottom: var(--space-2);
        }

        .specialist-list {
          display: flex;
          flex-direction: column;
          gap: var(--space-2);
        }

        .empty-specialists {
          text-align: center;
          color: var(--text-tertiary);
          font-size: var(--text-sm);
          padding: var(--space-4);
        }
      `})]})},b1=({status:e,results:t=[],onStart:n,onPause:r,onReset:i,loading:s=!1})=>{const a=(e==null?void 0:e.running)??!1,o=(e==null?void 0:e.progress)??0,l=e==null?void 0:e.current_task,u=d=>d?c.jsx(hu,{className:"icon-sm status-pass"}):c.jsx(pu,{className:"icon-sm status-fail"});return c.jsxs("div",{className:"benchmark-panel",children:[c.jsxs("div",{className:"benchmark-header",children:[c.jsx("h3",{className:"benchmark-title",children:"Benchmark Suite"}),c.jsxs("div",{className:"benchmark-actions",children:[a?c.jsx(ge,{variant:"warning",size:"sm",icon:a1,onClick:r,loading:s,children:"Pause"}):c.jsx(ge,{variant:"primary",size:"sm",icon:eg,onClick:n,loading:s,children:"Run All"}),c.jsx(ge,{variant:"ghost",size:"sm",icon:Fr,onClick:i,disabled:a||s,children:"Reset"})]})]}),a&&c.jsxs("div",{className:"benchmark-progress",children:[c.jsxs("div",{className:"progress-info",children:[c.jsx("span",{className:"progress-label",children:"Progress"}),c.jsxs("span",{className:"progress-value",children:[Math.round(o*100),"%"]})]}),c.jsx(us,{value:o*100,variant:"primary",animated:!0}),l&&c.jsxs("div",{className:"current-task",children:[c.jsx(gn,{className:"icon-xs"}),c.jsxs("span",{children:["Running: ",l]})]})]}),t.length>0&&c.jsxs("div",{className:"benchmark-results",children:[c.jsxs("div",{className:"results-header",children:[c.jsx("span",{children:"Recent Results"}),c.jsxs(cs,{variant:"info",size:"sm",children:[t.filter(d=>d.passed).length,"/",t.length," passed"]})]}),c.jsx("div",{className:"results-list",children:t.slice(0,5).map((d,h)=>c.jsxs("div",{className:"result-row",children:[u(d.passed),c.jsx("span",{className:"result-name",children:d.task_name}),c.jsx("span",{className:"result-score",children:(d.score||0).toFixed(3)}),c.jsxs("span",{className:"result-time",children:[(d.execution_time||0).toFixed(1),"s"]})]},h))})]}),!a&&t.length===0&&c.jsxs("div",{className:"benchmark-empty",children:[c.jsx("p",{children:"No benchmark results yet."}),c.jsx("p",{className:"empty-hint",children:'Click "Run All" to start the benchmark suite.'})]}),c.jsx("style",{children:`
        .benchmark-panel {
          background: var(--bg-secondary);
          border: 1px solid var(--border-primary);
          border-radius: var(--radius-lg);
          padding: var(--space-4);
        }

        .benchmark-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          margin-bottom: var(--space-4);
        }

        .benchmark-title {
          font-size: var(--text-md);
          font-weight: var(--weight-semibold);
          color: var(--text-primary);
        }

        .benchmark-actions {
          display: flex;
          gap: var(--space-2);
        }

        .benchmark-progress {
          padding: var(--space-3);
          background: var(--bg-tertiary);
          border-radius: var(--radius-md);
          margin-bottom: var(--space-4);
        }

        .progress-info {
          display: flex;
          justify-content: space-between;
          margin-bottom: var(--space-2);
        }

        .progress-label {
          font-size: var(--text-sm);
          color: var(--text-secondary);
        }

        .progress-value {
          font-size: var(--text-sm);
          font-weight: var(--weight-semibold);
          color: var(--accent-primary);
        }

        .current-task {
          display: flex;
          align-items: center;
          gap: var(--space-2);
          margin-top: var(--space-2);
          font-size: var(--text-xs);
          color: var(--text-tertiary);
        }

        .benchmark-results {
          border-top: 1px solid var(--border-primary);
          padding-top: var(--space-4);
        }

        .results-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: var(--space-3);
          font-size: var(--text-sm);
          color: var(--text-secondary);
        }

        .results-list {
          display: flex;
          flex-direction: column;
          gap: var(--space-2);
        }

        .result-row {
          display: flex;
          align-items: center;
          gap: var(--space-2);
          padding: var(--space-2);
          background: var(--bg-tertiary);
          border-radius: var(--radius-sm);
        }

        .status-pass {
          color: var(--accent-primary);
        }

        .status-fail {
          color: var(--accent-danger);
        }

        .result-name {
          flex: 1;
          font-size: var(--text-sm);
          color: var(--text-primary);
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }

        .result-score {
          font-family: var(--font-mono);
          font-size: var(--text-sm);
          font-weight: var(--weight-semibold);
          color: var(--accent-secondary);
        }

        .result-time {
          font-size: var(--text-xs);
          color: var(--text-tertiary);
          min-width: 40px;
          text-align: right;
        }

        .benchmark-empty {
          text-align: center;
          padding: var(--space-6);
          color: var(--text-secondary);
        }

        .empty-hint {
          font-size: var(--text-sm);
          color: var(--text-tertiary);
          margin-top: var(--space-2);
        }
      `})]})},lg=({tasks:e,onViewTask:t,onRetryTask:n,onDeleteTask:r,onFeedbackSubmitted:i,loading:s=!1,emptyMessage:a="No tasks to display"})=>{const[o,l]=_.useState(null),[u,d]=_.useState({}),h=async(y,g,x)=>{if(y.stopPropagation(),!u[g.id]){d(b=>({...b,[g.id]:"loading"}));try{await Ve.tasks.submitFeedback(g.id,{rating:x==="positive"?5:2,feedback_type:x==="positive"?"helpful":"other",would_use_again:x==="positive"}),d(b=>({...b,[g.id]:x})),i==null||i(g.id,x)}catch(b){console.error("Failed to submit feedback:",b),d(k=>{const w={...k};return delete w[g.id],w})}}},f=y=>{switch(y){case"completed":return c.jsx(hu,{className:"icon-sm status-completed"});case"failed":return c.jsx(pu,{className:"icon-sm status-failed"});case"running":return c.jsx(gn,{className:"icon-sm status-running"});case"pending":return c.jsx(Xm,{className:"icon-sm status-pending"});default:return null}},p=y=>y===void 0?"var(--text-tertiary)":y>=.85?"var(--accent-primary)":y>=.7?"var(--accent-secondary)":y>=.5?"var(--accent-warning)":"var(--accent-danger)",m=y=>new Date(y).toLocaleTimeString([],{hour:"2-digit",minute:"2-digit"}),v=y=>{if(!y)return"-";if(y<60)return`${y.toFixed(1)}s`;const g=Math.floor(y/60),x=y%60;return`${g}m ${x.toFixed(0)}s`};return s?c.jsxs("div",{className:"tasks-table",children:[c.jsx("div",{className:"tasks-loading",children:[...Array(5)].map((y,g)=>c.jsx("div",{className:"skeleton skeleton-row"},g))}),c.jsx("style",{children:Yo})]}):e.length===0?c.jsxs("div",{className:"tasks-table",children:[c.jsx("div",{className:"tasks-empty",children:c.jsx("p",{children:a})}),c.jsx("style",{children:Yo})]}):c.jsxs("div",{className:"tasks-table",children:[c.jsxs("table",{children:[c.jsx("thead",{children:c.jsxs("tr",{children:[c.jsx("th",{children:"Status"}),c.jsx("th",{children:"Task"}),c.jsx("th",{children:"Specialist"}),c.jsx("th",{children:"Score"}),c.jsx("th",{children:"Duration"}),c.jsx("th",{children:"Time"}),c.jsx("th",{children:"Feedback"}),c.jsx("th",{})]})}),c.jsx("tbody",{children:e.map(y=>c.jsxs("tr",{onClick:()=>t==null?void 0:t(y),children:[c.jsx("td",{children:c.jsx("div",{className:"status-cell",children:f(y.status)})}),c.jsx("td",{children:c.jsxs("div",{className:"task-cell",children:[c.jsx("span",{className:"task-name",children:y.task_name}),c.jsxs("span",{className:"task-id",children:["#",y.id.slice(0,8)]})]})}),c.jsx("td",{children:c.jsx("span",{className:"specialist-name",children:y.specialist_name||"-"})}),c.jsx("td",{children:c.jsx("span",{className:"score-value",style:{color:p(y.score)},children:y.score!==void 0?y.score.toFixed(3):"-"})}),c.jsx("td",{children:c.jsx("span",{className:"duration-value",children:v(y.duration)})}),c.jsx("td",{children:c.jsx("span",{className:"time-value",children:m(y.timestamp)})}),c.jsx("td",{children:c.jsx("div",{className:"feedback-cell",children:u[y.id]==="loading"?c.jsx("span",{className:"feedback-loading",children:"..."}):u[y.id]?c.jsx("span",{className:`feedback-given feedback-${u[y.id]}`,children:c.jsx(Km,{className:"icon-xs"})}):y.status==="completed"?c.jsxs(c.Fragment,{children:[c.jsx("button",{className:"feedback-btn feedback-positive",onClick:g=>h(g,y,"positive"),title:"Good response",children:c.jsx(ag,{className:"icon-xs"})}),c.jsx("button",{className:"feedback-btn feedback-negative",onClick:g=>h(g,y,"negative"),title:"Poor response",children:c.jsx(sg,{className:"icon-xs"})})]}):c.jsx("span",{className:"feedback-na",children:"-"})})}),c.jsx("td",{children:c.jsxs("div",{className:"actions-cell",children:[c.jsx("button",{className:"action-button",onClick:g=>{g.stopPropagation(),l(o===y.id?null:y.id)},children:c.jsx(s1,{className:"icon-sm"})}),o===y.id&&c.jsxs("div",{className:"action-menu",children:[c.jsxs("button",{onClick:g=>{g.stopPropagation(),t==null||t(y),l(null)},children:[c.jsx(t1,{className:"icon-xs"}),"View Details"]}),y.status==="failed"&&c.jsxs("button",{onClick:g=>{g.stopPropagation(),n==null||n(y),l(null)},children:[c.jsx(Fr,{className:"icon-xs"}),"Retry"]}),c.jsxs("button",{className:"delete",onClick:g=>{g.stopPropagation(),r==null||r(y),l(null)},children:[c.jsx(ls,{className:"icon-xs"}),"Delete"]})]})]})})]},y.id))})]}),c.jsx("style",{children:Yo})]})},Yo=`
  .tasks-table {
    background: var(--bg-secondary);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-lg);
    overflow: hidden;
  }

  .tasks-table table {
    width: 100%;
    border-collapse: collapse;
  }

  .tasks-table th {
    padding: var(--space-3) var(--space-4);
    text-align: left;
    font-size: var(--text-xs);
    font-weight: var(--weight-semibold);
    color: var(--text-tertiary);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    background: var(--bg-tertiary);
    border-bottom: 1px solid var(--border-primary);
  }

  .tasks-table td {
    padding: var(--space-3) var(--space-4);
    border-bottom: 1px solid var(--border-primary);
  }

  .tasks-table tbody tr {
    cursor: pointer;
    transition: background var(--transition-fast);
  }

  .tasks-table tbody tr:hover {
    background: var(--bg-hover);
  }

  .tasks-table tbody tr:last-child td {
    border-bottom: none;
  }

  .status-cell {
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .status-completed {
    color: var(--accent-primary);
  }

  .status-failed {
    color: var(--accent-danger);
  }

  .status-running {
    color: var(--accent-secondary);
    animation: spin 1s linear infinite;
  }

  .status-pending {
    color: var(--text-tertiary);
  }

  .task-cell {
    display: flex;
    flex-direction: column;
    gap: var(--space-1);
  }

  .task-name {
    font-size: var(--text-sm);
    color: var(--text-primary);
    font-weight: var(--weight-medium);
  }

  .task-id {
    font-family: var(--font-mono);
    font-size: var(--text-xs);
    color: var(--text-tertiary);
  }

  .specialist-name {
    font-size: var(--text-sm);
    color: var(--text-secondary);
  }

  .score-value {
    font-family: var(--font-mono);
    font-size: var(--text-sm);
    font-weight: var(--weight-semibold);
  }

  .duration-value {
    font-size: var(--text-sm);
    color: var(--text-secondary);
  }

  .time-value {
    font-size: var(--text-sm);
    color: var(--text-tertiary);
  }

  .actions-cell {
    position: relative;
  }

  .action-button {
    padding: var(--space-1);
    background: transparent;
    border: none;
    color: var(--text-tertiary);
    cursor: pointer;
    border-radius: var(--radius-sm);
    transition: all var(--transition-fast);
  }

  .action-button:hover {
    background: var(--bg-tertiary);
    color: var(--text-primary);
  }

  .action-menu {
    position: absolute;
    right: 0;
    top: 100%;
    background: var(--bg-secondary);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-md);
    box-shadow: var(--shadow-lg);
    z-index: var(--z-dropdown);
    min-width: 150px;
  }

  .action-menu button {
    display: flex;
    align-items: center;
    gap: var(--space-2);
    width: 100%;
    padding: var(--space-2) var(--space-3);
    background: transparent;
    border: none;
    color: var(--text-secondary);
    font-size: var(--text-sm);
    cursor: pointer;
    transition: all var(--transition-fast);
    text-align: left;
  }

  .action-menu button:hover {
    background: var(--bg-hover);
    color: var(--text-primary);
  }

  .action-menu button.delete:hover {
    background: var(--accent-danger-dim);
    color: var(--accent-danger);
  }

  .tasks-loading {
    padding: var(--space-4);
    display: flex;
    flex-direction: column;
    gap: var(--space-2);
  }

  .skeleton-row {
    height: 48px;
    border-radius: var(--radius-sm);
  }

  .tasks-empty {
    padding: var(--space-8);
    text-align: center;
    color: var(--text-tertiary);
  }

  .feedback-cell {
    display: flex;
    align-items: center;
    gap: var(--space-2);
    justify-content: center;
  }

  .feedback-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 28px;
    height: 28px;
    padding: 0;
    background: transparent;
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-sm);
    color: var(--text-tertiary);
    cursor: pointer;
    transition: all var(--transition-fast);
  }

  .feedback-btn:hover {
    border-color: var(--border-secondary);
    color: var(--text-primary);
  }

  .feedback-btn.feedback-positive:hover {
    background: var(--accent-primary-dim);
    border-color: var(--accent-primary);
    color: var(--accent-primary);
  }

  .feedback-btn.feedback-negative:hover {
    background: var(--accent-danger-dim);
    border-color: var(--accent-danger);
    color: var(--accent-danger);
  }

  .feedback-given {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 28px;
    height: 28px;
  }

  .feedback-given.feedback-positive {
    color: var(--accent-primary);
  }

  .feedback-given.feedback-negative {
    color: var(--accent-danger);
  }

  .feedback-loading {
    color: var(--text-tertiary);
    animation: pulse 1s ease-in-out infinite;
  }

  .feedback-na {
    color: var(--text-tertiary);
  }

  @keyframes pulse {
    0%, 100% { opacity: 0.4; }
    50% { opacity: 1; }
  }
`,k1=({taskId:e,specialistId:t,onFeedback:n,disabled:r=!1,showComment:i=!0,size:s="md"})=>{const[a,o]=_.useState(null),[l,u]=_.useState(!1),[d,h]=_.useState(""),[f,p]=_.useState(!1),m=y=>{r||f||(o(y),i?u(!0):v(y))},v=y=>{const g=y||a;g&&(n==null||n({taskId:e,specialistId:t,type:g,comment:d.trim()||void 0}),p(!0),u(!1))};return f?c.jsxs("div",{className:`feedback-buttons submitted ${s}`,children:[c.jsx("div",{className:"feedback-thanks",children:c.jsx("span",{children:"Thanks for your feedback!"})}),c.jsx("style",{children:Jd})]}):c.jsxs("div",{className:`feedback-buttons ${s}`,children:[c.jsxs("div",{className:"feedback-actions",children:[c.jsx("button",{className:`feedback-btn positive ${a==="positive"?"selected":""}`,onClick:()=>m("positive"),disabled:r,"aria-label":"Positive feedback",children:c.jsx(ag,{className:s==="sm"?"icon-sm":"icon"})}),c.jsx("button",{className:`feedback-btn negative ${a==="negative"?"selected":""}`,onClick:()=>m("negative"),disabled:r,"aria-label":"Negative feedback",children:c.jsx(sg,{className:s==="sm"?"icon-sm":"icon"})})]}),l&&c.jsxs("div",{className:"feedback-comment",children:[c.jsxs("div",{className:"comment-input-wrapper",children:[c.jsx(i1,{className:"icon-sm comment-icon"}),c.jsx("input",{type:"text",className:"comment-input",placeholder:"Add a comment (optional)",value:d,onChange:y=>h(y.target.value),onKeyDown:y=>y.key==="Enter"&&v(),autoFocus:!0}),c.jsx("button",{className:"comment-submit",onClick:()=>v(),"aria-label":"Submit feedback",children:c.jsx(rg,{className:"icon-sm"})})]}),c.jsx("button",{className:"comment-skip",onClick:()=>v(),children:"Skip"})]}),c.jsx("style",{children:Jd})]})},Jd=`
  .feedback-buttons {
    display: flex;
    flex-direction: column;
    gap: var(--space-2);
  }

  .feedback-buttons.sm {
    gap: var(--space-1);
  }

  .feedback-actions {
    display: flex;
    gap: var(--space-2);
  }

  .feedback-buttons.sm .feedback-actions {
    gap: var(--space-1);
  }

  .feedback-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    padding: var(--space-2);
    background: var(--bg-tertiary);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-md);
    color: var(--text-secondary);
    cursor: pointer;
    transition: all var(--transition-fast);
  }

  .feedback-buttons.sm .feedback-btn {
    padding: var(--space-1);
    border-radius: var(--radius-sm);
  }

  .feedback-btn:hover:not(:disabled) {
    border-color: var(--border-secondary);
    color: var(--text-primary);
  }

  .feedback-btn.positive:hover:not(:disabled),
  .feedback-btn.positive.selected {
    background: var(--accent-primary-dim);
    border-color: var(--accent-primary);
    color: var(--accent-primary);
  }

  .feedback-btn.negative:hover:not(:disabled),
  .feedback-btn.negative.selected {
    background: var(--accent-danger-dim);
    border-color: var(--accent-danger);
    color: var(--accent-danger);
  }

  .feedback-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .feedback-comment {
    display: flex;
    align-items: center;
    gap: var(--space-2);
    animation: fadeIn var(--transition-fast);
  }

  .comment-input-wrapper {
    flex: 1;
    display: flex;
    align-items: center;
    gap: var(--space-2);
    padding: var(--space-2);
    background: var(--bg-tertiary);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-md);
  }

  .comment-icon {
    color: var(--text-tertiary);
    flex-shrink: 0;
  }

  .comment-input {
    flex: 1;
    background: transparent;
    border: none;
    color: var(--text-primary);
    font-size: var(--text-sm);
    outline: none;
  }

  .comment-input::placeholder {
    color: var(--text-tertiary);
  }

  .comment-submit {
    padding: var(--space-1);
    background: var(--accent-primary);
    border: none;
    border-radius: var(--radius-sm);
    color: var(--bg-primary);
    cursor: pointer;
    transition: all var(--transition-fast);
    flex-shrink: 0;
  }

  .comment-submit:hover {
    opacity: 0.9;
  }

  .comment-skip {
    padding: var(--space-2);
    background: transparent;
    border: none;
    color: var(--text-tertiary);
    font-size: var(--text-sm);
    cursor: pointer;
    transition: color var(--transition-fast);
  }

  .comment-skip:hover {
    color: var(--text-secondary);
  }

  .feedback-thanks {
    display: flex;
    align-items: center;
    gap: var(--space-2);
    padding: var(--space-2);
    background: var(--accent-primary-dim);
    border-radius: var(--radius-md);
    color: var(--accent-primary);
    font-size: var(--text-sm);
  }
`,w1=({budget:e,onClick:t,compact:n=!1})=>{if(!e)return c.jsxs("div",{className:`budget-badge loading ${n?"compact":""}`,children:[c.jsx("div",{className:"skeleton skeleton-text",style:{width:"60px"}}),c.jsx("style",{children:Xo})]});const r=e.used||0,i=e.daily_limit||1,s=e.remaining||0,a=r/i*100,o=s<i*.2,l=s<i*.1,u=()=>l?"var(--accent-danger)":o?"var(--accent-warning)":"var(--accent-primary)",d=h=>`$${(h||0).toFixed(2)}`;return n?c.jsxs("div",{className:`budget-badge compact ${t?"clickable":""}`,onClick:t,role:t?"button":void 0,tabIndex:t?0:void 0,children:[c.jsx(Da,{className:"icon-sm",style:{color:u()}}),c.jsx("span",{className:"budget-amount",style:{color:u()},children:d(s)}),l&&c.jsx(rc,{className:"icon-xs warning-icon"}),c.jsx("style",{children:Xo})]}):c.jsxs("div",{className:`budget-badge ${t?"clickable":""}`,onClick:t,role:t?"button":void 0,tabIndex:t?0:void 0,children:[c.jsxs("div",{className:"budget-header",children:[c.jsx("div",{className:"budget-icon",children:c.jsx(Da,{className:"icon",style:{color:u()}})}),c.jsxs("div",{className:"budget-info",children:[c.jsx("div",{className:"budget-label",children:"Daily Budget"}),c.jsxs("div",{className:"budget-amounts",children:[c.jsx("span",{className:"budget-used",children:d(r)}),c.jsx("span",{className:"budget-separator",children:"/"}),c.jsx("span",{className:"budget-limit",children:d(i)})]})]}),(o||l)&&c.jsx(rc,{className:"icon warning-icon",style:{color:u()}})]}),c.jsx(us,{value:a,size:"sm",variant:l?"danger":o?"warning":"primary"}),c.jsxs("div",{className:"budget-footer",children:[c.jsxs("span",{className:"budget-remaining",children:[c.jsx("span",{style:{color:u()},children:d(s)})," ","remaining"]}),e.trend!==void 0&&c.jsxs("span",{className:`budget-trend ${e.trend>0?"up":"down"}`,children:[e.trend>0?c.jsx(Xn,{className:"icon-xs"}):c.jsx(Br,{className:"icon-xs"}),Math.abs(e.trend),"%"]})]}),c.jsx("style",{children:Xo})]})},Xo=`
  .budget-badge {
    background: var(--bg-secondary);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-lg);
    padding: var(--space-4);
  }

  .budget-badge.clickable {
    cursor: pointer;
    transition: all var(--transition-fast);
  }

  .budget-badge.clickable:hover {
    border-color: var(--border-secondary);
  }

  .budget-badge.compact {
    display: inline-flex;
    align-items: center;
    gap: var(--space-2);
    padding: var(--space-2) var(--space-3);
    border-radius: var(--radius-full);
    background: var(--bg-tertiary);
  }

  .budget-badge.compact .budget-amount {
    font-family: var(--font-mono);
    font-size: var(--text-sm);
    font-weight: var(--weight-semibold);
  }

  .budget-badge.loading {
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .budget-header {
    display: flex;
    align-items: center;
    gap: var(--space-3);
    margin-bottom: var(--space-3);
  }

  .budget-icon {
    width: 40px;
    height: 40px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--bg-tertiary);
    border-radius: var(--radius-md);
  }

  .budget-info {
    flex: 1;
  }

  .budget-label {
    font-size: var(--text-xs);
    color: var(--text-tertiary);
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .budget-amounts {
    font-family: var(--font-mono);
    font-size: var(--text-lg);
    font-weight: var(--weight-bold);
  }

  .budget-used {
    color: var(--text-primary);
  }

  .budget-separator {
    color: var(--text-tertiary);
    margin: 0 var(--space-1);
  }

  .budget-limit {
    color: var(--text-secondary);
  }

  .warning-icon {
    animation: pulse 2s ease-in-out infinite;
  }

  .budget-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: var(--space-3);
    font-size: var(--text-sm);
  }

  .budget-remaining {
    color: var(--text-secondary);
  }

  .budget-trend {
    display: flex;
    align-items: center;
    gap: var(--space-1);
    font-weight: var(--weight-medium);
  }

  .budget-trend.up {
    color: var(--accent-danger);
  }

  .budget-trend.down {
    color: var(--accent-primary);
  }
`;/*!
 * @kurkle/color v0.3.4
 * https://github.com/kurkle/color#readme
 * (c) 2024 Jukka Kurkela
 * Released under the MIT License
 */function hs(e){return e+.5|0}const en=(e,t,n)=>Math.max(Math.min(e,n),t);function li(e){return en(hs(e*2.55),0,255)}function fn(e){return en(hs(e*255),0,255)}function Rt(e){return en(hs(e/2.55)/100,0,1)}function eh(e){return en(hs(e*100),0,100)}const tt={0:0,1:1,2:2,3:3,4:4,5:5,6:6,7:7,8:8,9:9,A:10,B:11,C:12,D:13,E:14,F:15,a:10,b:11,c:12,d:13,e:14,f:15},sc=[..."0123456789ABCDEF"],_1=e=>sc[e&15],j1=e=>sc[(e&240)>>4]+sc[e&15],Ts=e=>(e&240)>>4===(e&15),S1=e=>Ts(e.r)&&Ts(e.g)&&Ts(e.b)&&Ts(e.a);function N1(e){var t=e.length,n;return e[0]==="#"&&(t===4||t===5?n={r:255&tt[e[1]]*17,g:255&tt[e[2]]*17,b:255&tt[e[3]]*17,a:t===5?tt[e[4]]*17:255}:(t===7||t===9)&&(n={r:tt[e[1]]<<4|tt[e[2]],g:tt[e[3]]<<4|tt[e[4]],b:tt[e[5]]<<4|tt[e[6]],a:t===9?tt[e[7]]<<4|tt[e[8]]:255})),n}const C1=(e,t)=>e<255?t(e):"";function M1(e){var t=S1(e)?_1:j1;return e?"#"+t(e.r)+t(e.g)+t(e.b)+C1(e.a,t):void 0}const P1=/^(hsla?|hwb|hsv)\(\s*([-+.e\d]+)(?:deg)?[\s,]+([-+.e\d]+)%[\s,]+([-+.e\d]+)%(?:[\s,]+([-+.e\d]+)(%)?)?\s*\)$/;function cg(e,t,n){const r=t*Math.min(n,1-n),i=(s,a=(s+e/30)%12)=>n-r*Math.max(Math.min(a-3,9-a,1),-1);return[i(0),i(8),i(4)]}function E1(e,t,n){const r=(i,s=(i+e/60)%6)=>n-n*t*Math.max(Math.min(s,4-s,1),0);return[r(5),r(3),r(1)]}function T1(e,t,n){const r=cg(e,1,.5);let i;for(t+n>1&&(i=1/(t+n),t*=i,n*=i),i=0;i<3;i++)r[i]*=1-t-n,r[i]+=t;return r}function z1(e,t,n,r,i){return e===i?(t-n)/r+(t<n?6:0):t===i?(n-e)/r+2:(e-t)/r+4}function vu(e){const n=e.r/255,r=e.g/255,i=e.b/255,s=Math.max(n,r,i),a=Math.min(n,r,i),o=(s+a)/2;let l,u,d;return s!==a&&(d=s-a,u=o>.5?d/(2-s-a):d/(s+a),l=z1(n,r,i,d,s),l=l*60+.5),[l|0,u||0,o]}function yu(e,t,n,r){return(Array.isArray(t)?e(t[0],t[1],t[2]):e(t,n,r)).map(fn)}function xu(e,t,n){return yu(cg,e,t,n)}function D1(e,t,n){return yu(T1,e,t,n)}function R1(e,t,n){return yu(E1,e,t,n)}function ug(e){return(e%360+360)%360}function L1(e){const t=P1.exec(e);let n=255,r;if(!t)return;t[5]!==r&&(n=t[6]?li(+t[5]):fn(+t[5]));const i=ug(+t[2]),s=+t[3]/100,a=+t[4]/100;return t[1]==="hwb"?r=D1(i,s,a):t[1]==="hsv"?r=R1(i,s,a):r=xu(i,s,a),{r:r[0],g:r[1],b:r[2],a:n}}function O1(e,t){var n=vu(e);n[0]=ug(n[0]+t),n=xu(n),e.r=n[0],e.g=n[1],e.b=n[2]}function A1(e){if(!e)return;const t=vu(e),n=t[0],r=eh(t[1]),i=eh(t[2]);return e.a<255?`hsla(${n}, ${r}%, ${i}%, ${Rt(e.a)})`:`hsl(${n}, ${r}%, ${i}%)`}const th={x:"dark",Z:"light",Y:"re",X:"blu",W:"gr",V:"medium",U:"slate",A:"ee",T:"ol",S:"or",B:"ra",C:"lateg",D:"ights",R:"in",Q:"turquois",E:"hi",P:"ro",O:"al",N:"le",M:"de",L:"yello",F:"en",K:"ch",G:"arks",H:"ea",I:"ightg",J:"wh"},nh={OiceXe:"f0f8ff",antiquewEte:"faebd7",aqua:"ffff",aquamarRe:"7fffd4",azuY:"f0ffff",beige:"f5f5dc",bisque:"ffe4c4",black:"0",blanKedOmond:"ffebcd",Xe:"ff",XeviTet:"8a2be2",bPwn:"a52a2a",burlywood:"deb887",caMtXe:"5f9ea0",KartYuse:"7fff00",KocTate:"d2691e",cSO:"ff7f50",cSnflowerXe:"6495ed",cSnsilk:"fff8dc",crimson:"dc143c",cyan:"ffff",xXe:"8b",xcyan:"8b8b",xgTMnPd:"b8860b",xWay:"a9a9a9",xgYF:"6400",xgYy:"a9a9a9",xkhaki:"bdb76b",xmagFta:"8b008b",xTivegYF:"556b2f",xSange:"ff8c00",xScEd:"9932cc",xYd:"8b0000",xsOmon:"e9967a",xsHgYF:"8fbc8f",xUXe:"483d8b",xUWay:"2f4f4f",xUgYy:"2f4f4f",xQe:"ced1",xviTet:"9400d3",dAppRk:"ff1493",dApskyXe:"bfff",dimWay:"696969",dimgYy:"696969",dodgerXe:"1e90ff",fiYbrick:"b22222",flSOwEte:"fffaf0",foYstWAn:"228b22",fuKsia:"ff00ff",gaRsbSo:"dcdcdc",ghostwEte:"f8f8ff",gTd:"ffd700",gTMnPd:"daa520",Way:"808080",gYF:"8000",gYFLw:"adff2f",gYy:"808080",honeyMw:"f0fff0",hotpRk:"ff69b4",RdianYd:"cd5c5c",Rdigo:"4b0082",ivSy:"fffff0",khaki:"f0e68c",lavFMr:"e6e6fa",lavFMrXsh:"fff0f5",lawngYF:"7cfc00",NmoncEffon:"fffacd",ZXe:"add8e6",ZcSO:"f08080",Zcyan:"e0ffff",ZgTMnPdLw:"fafad2",ZWay:"d3d3d3",ZgYF:"90ee90",ZgYy:"d3d3d3",ZpRk:"ffb6c1",ZsOmon:"ffa07a",ZsHgYF:"20b2aa",ZskyXe:"87cefa",ZUWay:"778899",ZUgYy:"778899",ZstAlXe:"b0c4de",ZLw:"ffffe0",lime:"ff00",limegYF:"32cd32",lRF:"faf0e6",magFta:"ff00ff",maPon:"800000",VaquamarRe:"66cdaa",VXe:"cd",VScEd:"ba55d3",VpurpN:"9370db",VsHgYF:"3cb371",VUXe:"7b68ee",VsprRggYF:"fa9a",VQe:"48d1cc",VviTetYd:"c71585",midnightXe:"191970",mRtcYam:"f5fffa",mistyPse:"ffe4e1",moccasR:"ffe4b5",navajowEte:"ffdead",navy:"80",Tdlace:"fdf5e6",Tive:"808000",TivedBb:"6b8e23",Sange:"ffa500",SangeYd:"ff4500",ScEd:"da70d6",pOegTMnPd:"eee8aa",pOegYF:"98fb98",pOeQe:"afeeee",pOeviTetYd:"db7093",papayawEp:"ffefd5",pHKpuff:"ffdab9",peru:"cd853f",pRk:"ffc0cb",plum:"dda0dd",powMrXe:"b0e0e6",purpN:"800080",YbeccapurpN:"663399",Yd:"ff0000",Psybrown:"bc8f8f",PyOXe:"4169e1",saddNbPwn:"8b4513",sOmon:"fa8072",sandybPwn:"f4a460",sHgYF:"2e8b57",sHshell:"fff5ee",siFna:"a0522d",silver:"c0c0c0",skyXe:"87ceeb",UXe:"6a5acd",UWay:"708090",UgYy:"708090",snow:"fffafa",sprRggYF:"ff7f",stAlXe:"4682b4",tan:"d2b48c",teO:"8080",tEstN:"d8bfd8",tomato:"ff6347",Qe:"40e0d0",viTet:"ee82ee",JHt:"f5deb3",wEte:"ffffff",wEtesmoke:"f5f5f5",Lw:"ffff00",LwgYF:"9acd32"};function I1(){const e={},t=Object.keys(nh),n=Object.keys(th);let r,i,s,a,o;for(r=0;r<t.length;r++){for(a=o=t[r],i=0;i<n.length;i++)s=n[i],o=o.replace(s,th[s]);s=parseInt(nh[a],16),e[o]=[s>>16&255,s>>8&255,s&255]}return e}let zs;function F1(e){zs||(zs=I1(),zs.transparent=[0,0,0,0]);const t=zs[e.toLowerCase()];return t&&{r:t[0],g:t[1],b:t[2],a:t.length===4?t[3]:255}}const B1=/^rgba?\(\s*([-+.\d]+)(%)?[\s,]+([-+.e\d]+)(%)?[\s,]+([-+.e\d]+)(%)?(?:[\s,/]+([-+.e\d]+)(%)?)?\s*\)$/;function $1(e){const t=B1.exec(e);let n=255,r,i,s;if(t){if(t[7]!==r){const a=+t[7];n=t[8]?li(a):en(a*255,0,255)}return r=+t[1],i=+t[3],s=+t[5],r=255&(t[2]?li(r):en(r,0,255)),i=255&(t[4]?li(i):en(i,0,255)),s=255&(t[6]?li(s):en(s,0,255)),{r,g:i,b:s,a:n}}}function H1(e){return e&&(e.a<255?`rgba(${e.r}, ${e.g}, ${e.b}, ${Rt(e.a)})`:`rgb(${e.r}, ${e.g}, ${e.b})`)}const Ko=e=>e<=.0031308?e*12.92:Math.pow(e,1/2.4)*1.055-.055,er=e=>e<=.04045?e/12.92:Math.pow((e+.055)/1.055,2.4);function W1(e,t,n){const r=er(Rt(e.r)),i=er(Rt(e.g)),s=er(Rt(e.b));return{r:fn(Ko(r+n*(er(Rt(t.r))-r))),g:fn(Ko(i+n*(er(Rt(t.g))-i))),b:fn(Ko(s+n*(er(Rt(t.b))-s))),a:e.a+n*(t.a-e.a)}}function Ds(e,t,n){if(e){let r=vu(e);r[t]=Math.max(0,Math.min(r[t]+r[t]*n,t===0?360:1)),r=xu(r),e.r=r[0],e.g=r[1],e.b=r[2]}}function dg(e,t){return e&&Object.assign(t||{},e)}function rh(e){var t={r:0,g:0,b:0,a:255};return Array.isArray(e)?e.length>=3&&(t={r:e[0],g:e[1],b:e[2],a:255},e.length>3&&(t.a=fn(e[3]))):(t=dg(e,{r:0,g:0,b:0,a:1}),t.a=fn(t.a)),t}function V1(e){return e.charAt(0)==="r"?$1(e):L1(e)}class Ki{constructor(t){if(t instanceof Ki)return t;const n=typeof t;let r;n==="object"?r=rh(t):n==="string"&&(r=N1(t)||F1(t)||V1(t)),this._rgb=r,this._valid=!!r}get valid(){return this._valid}get rgb(){var t=dg(this._rgb);return t&&(t.a=Rt(t.a)),t}set rgb(t){this._rgb=rh(t)}rgbString(){return this._valid?H1(this._rgb):void 0}hexString(){return this._valid?M1(this._rgb):void 0}hslString(){return this._valid?A1(this._rgb):void 0}mix(t,n){if(t){const r=this.rgb,i=t.rgb;let s;const a=n===s?.5:n,o=2*a-1,l=r.a-i.a,u=((o*l===-1?o:(o+l)/(1+o*l))+1)/2;s=1-u,r.r=255&u*r.r+s*i.r+.5,r.g=255&u*r.g+s*i.g+.5,r.b=255&u*r.b+s*i.b+.5,r.a=a*r.a+(1-a)*i.a,this.rgb=r}return this}interpolate(t,n){return t&&(this._rgb=W1(this._rgb,t._rgb,n)),this}clone(){return new Ki(this.rgb)}alpha(t){return this._rgb.a=fn(t),this}clearer(t){const n=this._rgb;return n.a*=1-t,this}greyscale(){const t=this._rgb,n=hs(t.r*.3+t.g*.59+t.b*.11);return t.r=t.g=t.b=n,this}opaquer(t){const n=this._rgb;return n.a*=1+t,this}negate(){const t=this._rgb;return t.r=255-t.r,t.g=255-t.g,t.b=255-t.b,this}lighten(t){return Ds(this._rgb,2,t),this}darken(t){return Ds(this._rgb,2,-t),this}saturate(t){return Ds(this._rgb,1,t),this}desaturate(t){return Ds(this._rgb,1,-t),this}rotate(t){return O1(this._rgb,t),this}}/*!
 * Chart.js v4.5.1
 * https://www.chartjs.org
 * (c) 2025 Chart.js Contributors
 * Released under the MIT License
 */function Mt(){}const U1=(()=>{let e=0;return()=>e++})();function Z(e){return e==null}function pe(e){if(Array.isArray&&Array.isArray(e))return!0;const t=Object.prototype.toString.call(e);return t.slice(0,7)==="[object"&&t.slice(-6)==="Array]"}function $(e){return e!==null&&Object.prototype.toString.call(e)==="[object Object]"}function De(e){return(typeof e=="number"||e instanceof Number)&&isFinite(+e)}function bt(e,t){return De(e)?e:t}function B(e,t){return typeof e>"u"?t:e}const Y1=(e,t)=>typeof e=="string"&&e.endsWith("%")?parseFloat(e)/100*t:+e;function te(e,t,n){if(e&&typeof e.call=="function")return e.apply(n,t)}function Y(e,t,n,r){let i,s,a;if(pe(e))for(s=e.length,i=0;i<s;i++)t.call(n,e[i],i);else if($(e))for(a=Object.keys(e),s=a.length,i=0;i<s;i++)t.call(n,e[a[i]],a[i])}function Ra(e,t){let n,r,i,s;if(!e||!t||e.length!==t.length)return!1;for(n=0,r=e.length;n<r;++n)if(i=e[n],s=t[n],i.datasetIndex!==s.datasetIndex||i.index!==s.index)return!1;return!0}function La(e){if(pe(e))return e.map(La);if($(e)){const t=Object.create(null),n=Object.keys(e),r=n.length;let i=0;for(;i<r;++i)t[n[i]]=La(e[n[i]]);return t}return e}function hg(e){return["__proto__","prototype","constructor"].indexOf(e)===-1}function X1(e,t,n,r){if(!hg(e))return;const i=t[e],s=n[e];$(i)&&$(s)?Qi(i,s,r):t[e]=La(s)}function Qi(e,t,n){const r=pe(t)?t:[t],i=r.length;if(!$(e))return e;n=n||{};const s=n.merger||X1;let a;for(let o=0;o<i;++o){if(a=r[o],!$(a))continue;const l=Object.keys(a);for(let u=0,d=l.length;u<d;++u)s(l[u],e,a,n)}return e}function ki(e,t){return Qi(e,t,{merger:K1})}function K1(e,t,n){if(!hg(e))return;const r=t[e],i=n[e];$(r)&&$(i)?ki(r,i):Object.prototype.hasOwnProperty.call(t,e)||(t[e]=La(i))}const ih={"":e=>e,x:e=>e.x,y:e=>e.y};function Q1(e){const t=e.split("."),n=[];let r="";for(const i of t)r+=i,r.endsWith("\\")?r=r.slice(0,-1)+".":(n.push(r),r="");return n}function G1(e){const t=Q1(e);return n=>{for(const r of t){if(r==="")break;n=n&&n[r]}return n}}function Oa(e,t){return(ih[t]||(ih[t]=G1(t)))(e)}function bu(e){return e.charAt(0).toUpperCase()+e.slice(1)}const Aa=e=>typeof e<"u",vn=e=>typeof e=="function",sh=(e,t)=>{if(e.size!==t.size)return!1;for(const n of e)if(!t.has(n))return!1;return!0};function Z1(e){return e.type==="mouseup"||e.type==="click"||e.type==="contextmenu"}const Q=Math.PI,be=2*Q,q1=be+Q,Ia=Number.POSITIVE_INFINITY,J1=Q/180,we=Q/2,wn=Q/4,ah=Q*2/3,fg=Math.log10,zr=Math.sign;function wi(e,t,n){return Math.abs(e-t)<n}function oh(e){const t=Math.round(e);e=wi(e,t,e/1e3)?t:e;const n=Math.pow(10,Math.floor(fg(e))),r=e/n;return(r<=1?1:r<=2?2:r<=5?5:10)*n}function eb(e){const t=[],n=Math.sqrt(e);let r;for(r=1;r<n;r++)e%r===0&&(t.push(r),t.push(e/r));return n===(n|0)&&t.push(n),t.sort((i,s)=>i-s).pop(),t}function tb(e){return typeof e=="symbol"||typeof e=="object"&&e!==null&&!(Symbol.toPrimitive in e||"toString"in e||"valueOf"in e)}function Gi(e){return!tb(e)&&!isNaN(parseFloat(e))&&isFinite(e)}function nb(e,t){const n=Math.round(e);return n-t<=e&&n+t>=e}function rb(e,t,n){let r,i,s;for(r=0,i=e.length;r<i;r++)s=e[r][n],isNaN(s)||(t.min=Math.min(t.min,s),t.max=Math.max(t.max,s))}function Dn(e){return e*(Q/180)}function ib(e){return e*(180/Q)}function lh(e){if(!De(e))return;let t=1,n=0;for(;Math.round(e*t)/t!==e;)t*=10,n++;return n}function pg(e,t){const n=t.x-e.x,r=t.y-e.y,i=Math.sqrt(n*n+r*r);let s=Math.atan2(r,n);return s<-.5*Q&&(s+=be),{angle:s,distance:i}}function ac(e,t){return Math.sqrt(Math.pow(t.x-e.x,2)+Math.pow(t.y-e.y,2))}function sb(e,t){return(e-t+q1)%be-Q}function Qe(e){return(e%be+be)%be}function ku(e,t,n,r){const i=Qe(e),s=Qe(t),a=Qe(n),o=Qe(s-i),l=Qe(a-i),u=Qe(i-s),d=Qe(i-a);return i===s||i===a||r&&s===a||o>l&&u<d}function Pe(e,t,n){return Math.max(t,Math.min(n,e))}function ab(e){return Pe(e,-32768,32767)}function At(e,t,n,r=1e-6){return e>=Math.min(t,n)-r&&e<=Math.max(t,n)+r}function wu(e,t,n){n=n||(a=>e[a]<t);let r=e.length-1,i=0,s;for(;r-i>1;)s=i+r>>1,n(s)?i=s:r=s;return{lo:i,hi:r}}const Rn=(e,t,n,r)=>wu(e,n,r?i=>{const s=e[i][t];return s<n||s===n&&e[i+1][t]===n}:i=>e[i][t]<n),ob=(e,t,n)=>wu(e,n,r=>e[r][t]>=n);function lb(e,t,n){let r=0,i=e.length;for(;r<i&&e[r]<t;)r++;for(;i>r&&e[i-1]>n;)i--;return r>0||i<e.length?e.slice(r,i):e}const mg=["push","pop","shift","splice","unshift"];function cb(e,t){if(e._chartjs){e._chartjs.listeners.push(t);return}Object.defineProperty(e,"_chartjs",{configurable:!0,enumerable:!1,value:{listeners:[t]}}),mg.forEach(n=>{const r="_onData"+bu(n),i=e[n];Object.defineProperty(e,n,{configurable:!0,enumerable:!1,value(...s){const a=i.apply(this,s);return e._chartjs.listeners.forEach(o=>{typeof o[r]=="function"&&o[r](...s)}),a}})})}function ch(e,t){const n=e._chartjs;if(!n)return;const r=n.listeners,i=r.indexOf(t);i!==-1&&r.splice(i,1),!(r.length>0)&&(mg.forEach(s=>{delete e[s]}),delete e._chartjs)}function ub(e){const t=new Set(e);return t.size===e.length?e:Array.from(t)}const gg=function(){return typeof window>"u"?function(e){return e()}:window.requestAnimationFrame}();function vg(e,t){let n=[],r=!1;return function(...i){n=i,r||(r=!0,gg.call(window,()=>{r=!1,e.apply(t,n)}))}}function db(e,t){let n;return function(...r){return t?(clearTimeout(n),n=setTimeout(e,t,r)):e.apply(this,r),t}}const _u=e=>e==="start"?"left":e==="end"?"right":"center",Ce=(e,t,n)=>e==="start"?t:e==="end"?n:(t+n)/2,hb=(e,t,n,r)=>e===(r?"left":"right")?n:e==="center"?(t+n)/2:t;function fb(e,t,n){const r=t.length;let i=0,s=r;if(e._sorted){const{iScale:a,vScale:o,_parsed:l}=e,u=e.dataset&&e.dataset.options?e.dataset.options.spanGaps:null,d=a.axis,{min:h,max:f,minDefined:p,maxDefined:m}=a.getUserBounds();if(p){if(i=Math.min(Rn(l,d,h).lo,n?r:Rn(t,d,a.getPixelForValue(h)).lo),u){const v=l.slice(0,i+1).reverse().findIndex(y=>!Z(y[o.axis]));i-=Math.max(0,v)}i=Pe(i,0,r-1)}if(m){let v=Math.max(Rn(l,a.axis,f,!0).hi+1,n?0:Rn(t,d,a.getPixelForValue(f),!0).hi+1);if(u){const y=l.slice(v-1).findIndex(g=>!Z(g[o.axis]));v+=Math.max(0,y)}s=Pe(v,i,r)-i}else s=r-i}return{start:i,count:s}}function pb(e){const{xScale:t,yScale:n,_scaleRanges:r}=e,i={xmin:t.min,xmax:t.max,ymin:n.min,ymax:n.max};if(!r)return e._scaleRanges=i,!0;const s=r.xmin!==t.min||r.xmax!==t.max||r.ymin!==n.min||r.ymax!==n.max;return Object.assign(r,i),s}const Rs=e=>e===0||e===1,uh=(e,t,n)=>-(Math.pow(2,10*(e-=1))*Math.sin((e-t)*be/n)),dh=(e,t,n)=>Math.pow(2,-10*e)*Math.sin((e-t)*be/n)+1,_i={linear:e=>e,easeInQuad:e=>e*e,easeOutQuad:e=>-e*(e-2),easeInOutQuad:e=>(e/=.5)<1?.5*e*e:-.5*(--e*(e-2)-1),easeInCubic:e=>e*e*e,easeOutCubic:e=>(e-=1)*e*e+1,easeInOutCubic:e=>(e/=.5)<1?.5*e*e*e:.5*((e-=2)*e*e+2),easeInQuart:e=>e*e*e*e,easeOutQuart:e=>-((e-=1)*e*e*e-1),easeInOutQuart:e=>(e/=.5)<1?.5*e*e*e*e:-.5*((e-=2)*e*e*e-2),easeInQuint:e=>e*e*e*e*e,easeOutQuint:e=>(e-=1)*e*e*e*e+1,easeInOutQuint:e=>(e/=.5)<1?.5*e*e*e*e*e:.5*((e-=2)*e*e*e*e+2),easeInSine:e=>-Math.cos(e*we)+1,easeOutSine:e=>Math.sin(e*we),easeInOutSine:e=>-.5*(Math.cos(Q*e)-1),easeInExpo:e=>e===0?0:Math.pow(2,10*(e-1)),easeOutExpo:e=>e===1?1:-Math.pow(2,-10*e)+1,easeInOutExpo:e=>Rs(e)?e:e<.5?.5*Math.pow(2,10*(e*2-1)):.5*(-Math.pow(2,-10*(e*2-1))+2),easeInCirc:e=>e>=1?e:-(Math.sqrt(1-e*e)-1),easeOutCirc:e=>Math.sqrt(1-(e-=1)*e),easeInOutCirc:e=>(e/=.5)<1?-.5*(Math.sqrt(1-e*e)-1):.5*(Math.sqrt(1-(e-=2)*e)+1),easeInElastic:e=>Rs(e)?e:uh(e,.075,.3),easeOutElastic:e=>Rs(e)?e:dh(e,.075,.3),easeInOutElastic(e){return Rs(e)?e:e<.5?.5*uh(e*2,.1125,.45):.5+.5*dh(e*2-1,.1125,.45)},easeInBack(e){return e*e*((1.70158+1)*e-1.70158)},easeOutBack(e){return(e-=1)*e*((1.70158+1)*e+1.70158)+1},easeInOutBack(e){let t=1.70158;return(e/=.5)<1?.5*(e*e*(((t*=1.525)+1)*e-t)):.5*((e-=2)*e*(((t*=1.525)+1)*e+t)+2)},easeInBounce:e=>1-_i.easeOutBounce(1-e),easeOutBounce(e){return e<1/2.75?7.5625*e*e:e<2/2.75?7.5625*(e-=1.5/2.75)*e+.75:e<2.5/2.75?7.5625*(e-=2.25/2.75)*e+.9375:7.5625*(e-=2.625/2.75)*e+.984375},easeInOutBounce:e=>e<.5?_i.easeInBounce(e*2)*.5:_i.easeOutBounce(e*2-1)*.5+.5};function ju(e){if(e&&typeof e=="object"){const t=e.toString();return t==="[object CanvasPattern]"||t==="[object CanvasGradient]"}return!1}function hh(e){return ju(e)?e:new Ki(e)}function Qo(e){return ju(e)?e:new Ki(e).saturate(.5).darken(.1).hexString()}const mb=["x","y","borderWidth","radius","tension"],gb=["color","borderColor","backgroundColor"];function vb(e){e.set("animation",{delay:void 0,duration:1e3,easing:"easeOutQuart",fn:void 0,from:void 0,loop:void 0,to:void 0,type:void 0}),e.describe("animation",{_fallback:!1,_indexable:!1,_scriptable:t=>t!=="onProgress"&&t!=="onComplete"&&t!=="fn"}),e.set("animations",{colors:{type:"color",properties:gb},numbers:{type:"number",properties:mb}}),e.describe("animations",{_fallback:"animation"}),e.set("transitions",{active:{animation:{duration:400}},resize:{animation:{duration:0}},show:{animations:{colors:{from:"transparent"},visible:{type:"boolean",duration:0}}},hide:{animations:{colors:{to:"transparent"},visible:{type:"boolean",easing:"linear",fn:t=>t|0}}}})}function yb(e){e.set("layout",{autoPadding:!0,padding:{top:0,right:0,bottom:0,left:0}})}const fh=new Map;function xb(e,t){t=t||{};const n=e+JSON.stringify(t);let r=fh.get(n);return r||(r=new Intl.NumberFormat(e,t),fh.set(n,r)),r}function yg(e,t,n){return xb(t,n).format(e)}const bb={values(e){return pe(e)?e:""+e},numeric(e,t,n){if(e===0)return"0";const r=this.chart.options.locale;let i,s=e;if(n.length>1){const u=Math.max(Math.abs(n[0].value),Math.abs(n[n.length-1].value));(u<1e-4||u>1e15)&&(i="scientific"),s=kb(e,n)}const a=fg(Math.abs(s)),o=isNaN(a)?1:Math.max(Math.min(-1*Math.floor(a),20),0),l={notation:i,minimumFractionDigits:o,maximumFractionDigits:o};return Object.assign(l,this.options.ticks.format),yg(e,r,l)}};function kb(e,t){let n=t.length>3?t[2].value-t[1].value:t[1].value-t[0].value;return Math.abs(n)>=1&&e!==Math.floor(e)&&(n=e-Math.floor(e)),n}var xg={formatters:bb};function wb(e){e.set("scale",{display:!0,offset:!1,reverse:!1,beginAtZero:!1,bounds:"ticks",clip:!0,grace:0,grid:{display:!0,lineWidth:1,drawOnChartArea:!0,drawTicks:!0,tickLength:8,tickWidth:(t,n)=>n.lineWidth,tickColor:(t,n)=>n.color,offset:!1},border:{display:!0,dash:[],dashOffset:0,width:1},title:{display:!1,text:"",padding:{top:4,bottom:4}},ticks:{minRotation:0,maxRotation:50,mirror:!1,textStrokeWidth:0,textStrokeColor:"",padding:3,display:!0,autoSkip:!0,autoSkipPadding:3,labelOffset:0,callback:xg.formatters.values,minor:{},major:{},align:"center",crossAlign:"near",showLabelBackdrop:!1,backdropColor:"rgba(255, 255, 255, 0.75)",backdropPadding:2}}),e.route("scale.ticks","color","","color"),e.route("scale.grid","color","","borderColor"),e.route("scale.border","color","","borderColor"),e.route("scale.title","color","","color"),e.describe("scale",{_fallback:!1,_scriptable:t=>!t.startsWith("before")&&!t.startsWith("after")&&t!=="callback"&&t!=="parser",_indexable:t=>t!=="borderDash"&&t!=="tickBorderDash"&&t!=="dash"}),e.describe("scales",{_fallback:"scale"}),e.describe("scale.ticks",{_scriptable:t=>t!=="backdropPadding"&&t!=="callback",_indexable:t=>t!=="backdropPadding"})}const Kn=Object.create(null),oc=Object.create(null);function ji(e,t){if(!t)return e;const n=t.split(".");for(let r=0,i=n.length;r<i;++r){const s=n[r];e=e[s]||(e[s]=Object.create(null))}return e}function Go(e,t,n){return typeof t=="string"?Qi(ji(e,t),n):Qi(ji(e,""),t)}class _b{constructor(t,n){this.animation=void 0,this.backgroundColor="rgba(0,0,0,0.1)",this.borderColor="rgba(0,0,0,0.1)",this.color="#666",this.datasets={},this.devicePixelRatio=r=>r.chart.platform.getDevicePixelRatio(),this.elements={},this.events=["mousemove","mouseout","click","touchstart","touchmove"],this.font={family:"'Helvetica Neue', 'Helvetica', 'Arial', sans-serif",size:12,style:"normal",lineHeight:1.2,weight:null},this.hover={},this.hoverBackgroundColor=(r,i)=>Qo(i.backgroundColor),this.hoverBorderColor=(r,i)=>Qo(i.borderColor),this.hoverColor=(r,i)=>Qo(i.color),this.indexAxis="x",this.interaction={mode:"nearest",intersect:!0,includeInvisible:!1},this.maintainAspectRatio=!0,this.onHover=null,this.onClick=null,this.parsing=!0,this.plugins={},this.responsive=!0,this.scale=void 0,this.scales={},this.showLine=!0,this.drawActiveElementsOnTop=!0,this.describe(t),this.apply(n)}set(t,n){return Go(this,t,n)}get(t){return ji(this,t)}describe(t,n){return Go(oc,t,n)}override(t,n){return Go(Kn,t,n)}route(t,n,r,i){const s=ji(this,t),a=ji(this,r),o="_"+n;Object.defineProperties(s,{[o]:{value:s[n],writable:!0},[n]:{enumerable:!0,get(){const l=this[o],u=a[i];return $(l)?Object.assign({},u,l):B(l,u)},set(l){this[o]=l}}})}apply(t){t.forEach(n=>n(this))}}var ue=new _b({_scriptable:e=>!e.startsWith("on"),_indexable:e=>e!=="events",hover:{_fallback:"interaction"},interaction:{_scriptable:!1,_indexable:!1}},[vb,yb,wb]);function jb(e){return!e||Z(e.size)||Z(e.family)?null:(e.style?e.style+" ":"")+(e.weight?e.weight+" ":"")+e.size+"px "+e.family}function ph(e,t,n,r,i){let s=t[i];return s||(s=t[i]=e.measureText(i).width,n.push(i)),s>r&&(r=s),r}function _n(e,t,n){const r=e.currentDevicePixelRatio,i=n!==0?Math.max(n/2,.5):0;return Math.round((t-i)*r)/r+i}function mh(e,t){!t&&!e||(t=t||e.getContext("2d"),t.save(),t.resetTransform(),t.clearRect(0,0,e.width,e.height),t.restore())}function lc(e,t,n,r){bg(e,t,n,r,null)}function bg(e,t,n,r,i){let s,a,o,l,u,d,h,f;const p=t.pointStyle,m=t.rotation,v=t.radius;let y=(m||0)*J1;if(p&&typeof p=="object"&&(s=p.toString(),s==="[object HTMLImageElement]"||s==="[object HTMLCanvasElement]")){e.save(),e.translate(n,r),e.rotate(y),e.drawImage(p,-p.width/2,-p.height/2,p.width,p.height),e.restore();return}if(!(isNaN(v)||v<=0)){switch(e.beginPath(),p){default:i?e.ellipse(n,r,i/2,v,0,0,be):e.arc(n,r,v,0,be),e.closePath();break;case"triangle":d=i?i/2:v,e.moveTo(n+Math.sin(y)*d,r-Math.cos(y)*v),y+=ah,e.lineTo(n+Math.sin(y)*d,r-Math.cos(y)*v),y+=ah,e.lineTo(n+Math.sin(y)*d,r-Math.cos(y)*v),e.closePath();break;case"rectRounded":u=v*.516,l=v-u,a=Math.cos(y+wn)*l,h=Math.cos(y+wn)*(i?i/2-u:l),o=Math.sin(y+wn)*l,f=Math.sin(y+wn)*(i?i/2-u:l),e.arc(n-h,r-o,u,y-Q,y-we),e.arc(n+f,r-a,u,y-we,y),e.arc(n+h,r+o,u,y,y+we),e.arc(n-f,r+a,u,y+we,y+Q),e.closePath();break;case"rect":if(!m){l=Math.SQRT1_2*v,d=i?i/2:l,e.rect(n-d,r-l,2*d,2*l);break}y+=wn;case"rectRot":h=Math.cos(y)*(i?i/2:v),a=Math.cos(y)*v,o=Math.sin(y)*v,f=Math.sin(y)*(i?i/2:v),e.moveTo(n-h,r-o),e.lineTo(n+f,r-a),e.lineTo(n+h,r+o),e.lineTo(n-f,r+a),e.closePath();break;case"crossRot":y+=wn;case"cross":h=Math.cos(y)*(i?i/2:v),a=Math.cos(y)*v,o=Math.sin(y)*v,f=Math.sin(y)*(i?i/2:v),e.moveTo(n-h,r-o),e.lineTo(n+h,r+o),e.moveTo(n+f,r-a),e.lineTo(n-f,r+a);break;case"star":h=Math.cos(y)*(i?i/2:v),a=Math.cos(y)*v,o=Math.sin(y)*v,f=Math.sin(y)*(i?i/2:v),e.moveTo(n-h,r-o),e.lineTo(n+h,r+o),e.moveTo(n+f,r-a),e.lineTo(n-f,r+a),y+=wn,h=Math.cos(y)*(i?i/2:v),a=Math.cos(y)*v,o=Math.sin(y)*v,f=Math.sin(y)*(i?i/2:v),e.moveTo(n-h,r-o),e.lineTo(n+h,r+o),e.moveTo(n+f,r-a),e.lineTo(n-f,r+a);break;case"line":a=i?i/2:Math.cos(y)*v,o=Math.sin(y)*v,e.moveTo(n-a,r-o),e.lineTo(n+a,r+o);break;case"dash":e.moveTo(n,r),e.lineTo(n+Math.cos(y)*(i?i/2:v),r+Math.sin(y)*v);break;case!1:e.closePath();break}e.fill(),t.borderWidth>0&&e.stroke()}}function Zi(e,t,n){return n=n||.5,!t||e&&e.x>t.left-n&&e.x<t.right+n&&e.y>t.top-n&&e.y<t.bottom+n}function uo(e,t){e.save(),e.beginPath(),e.rect(t.left,t.top,t.right-t.left,t.bottom-t.top),e.clip()}function ho(e){e.restore()}function Sb(e,t,n,r,i){if(!t)return e.lineTo(n.x,n.y);if(i==="middle"){const s=(t.x+n.x)/2;e.lineTo(s,t.y),e.lineTo(s,n.y)}else i==="after"!=!!r?e.lineTo(t.x,n.y):e.lineTo(n.x,t.y);e.lineTo(n.x,n.y)}function Nb(e,t,n,r){if(!t)return e.lineTo(n.x,n.y);e.bezierCurveTo(r?t.cp1x:t.cp2x,r?t.cp1y:t.cp2y,r?n.cp2x:n.cp1x,r?n.cp2y:n.cp1y,n.x,n.y)}function Cb(e,t){t.translation&&e.translate(t.translation[0],t.translation[1]),Z(t.rotation)||e.rotate(t.rotation),t.color&&(e.fillStyle=t.color),t.textAlign&&(e.textAlign=t.textAlign),t.textBaseline&&(e.textBaseline=t.textBaseline)}function Mb(e,t,n,r,i){if(i.strikethrough||i.underline){const s=e.measureText(r),a=t-s.actualBoundingBoxLeft,o=t+s.actualBoundingBoxRight,l=n-s.actualBoundingBoxAscent,u=n+s.actualBoundingBoxDescent,d=i.strikethrough?(l+u)/2:u;e.strokeStyle=e.fillStyle,e.beginPath(),e.lineWidth=i.decorationWidth||2,e.moveTo(a,d),e.lineTo(o,d),e.stroke()}}function Pb(e,t){const n=e.fillStyle;e.fillStyle=t.color,e.fillRect(t.left,t.top,t.width,t.height),e.fillStyle=n}function qi(e,t,n,r,i,s={}){const a=pe(t)?t:[t],o=s.strokeWidth>0&&s.strokeColor!=="";let l,u;for(e.save(),e.font=i.string,Cb(e,s),l=0;l<a.length;++l)u=a[l],s.backdrop&&Pb(e,s.backdrop),o&&(s.strokeColor&&(e.strokeStyle=s.strokeColor),Z(s.strokeWidth)||(e.lineWidth=s.strokeWidth),e.strokeText(u,n,r,s.maxWidth)),e.fillText(u,n,r,s.maxWidth),Mb(e,n,r,u,s),r+=Number(i.lineHeight);e.restore()}function Fa(e,t){const{x:n,y:r,w:i,h:s,radius:a}=t;e.arc(n+a.topLeft,r+a.topLeft,a.topLeft,1.5*Q,Q,!0),e.lineTo(n,r+s-a.bottomLeft),e.arc(n+a.bottomLeft,r+s-a.bottomLeft,a.bottomLeft,Q,we,!0),e.lineTo(n+i-a.bottomRight,r+s),e.arc(n+i-a.bottomRight,r+s-a.bottomRight,a.bottomRight,we,0,!0),e.lineTo(n+i,r+a.topRight),e.arc(n+i-a.topRight,r+a.topRight,a.topRight,0,-we,!0),e.lineTo(n+a.topLeft,r)}const Eb=/^(normal|(\d+(?:\.\d+)?)(px|em|%)?)$/,Tb=/^(normal|italic|initial|inherit|unset|(oblique( -?[0-9]?[0-9]deg)?))$/;function zb(e,t){const n=(""+e).match(Eb);if(!n||n[1]==="normal")return t*1.2;switch(e=+n[2],n[3]){case"px":return e;case"%":e/=100;break}return t*e}const Db=e=>+e||0;function Su(e,t){const n={},r=$(t),i=r?Object.keys(t):t,s=$(e)?r?a=>B(e[a],e[t[a]]):a=>e[a]:()=>e;for(const a of i)n[a]=Db(s(a));return n}function kg(e){return Su(e,{top:"y",right:"x",bottom:"y",left:"x"})}function wr(e){return Su(e,["topLeft","topRight","bottomLeft","bottomRight"])}function ct(e){const t=kg(e);return t.width=t.left+t.right,t.height=t.top+t.bottom,t}function Ee(e,t){e=e||{},t=t||ue.font;let n=B(e.size,t.size);typeof n=="string"&&(n=parseInt(n,10));let r=B(e.style,t.style);r&&!(""+r).match(Tb)&&(console.warn('Invalid font style specified: "'+r+'"'),r=void 0);const i={family:B(e.family,t.family),lineHeight:zb(B(e.lineHeight,t.lineHeight),n),size:n,style:r,weight:B(e.weight,t.weight),string:""};return i.string=jb(i),i}function Ls(e,t,n,r){let i,s,a;for(i=0,s=e.length;i<s;++i)if(a=e[i],a!==void 0&&a!==void 0)return a}function Rb(e,t,n){const{min:r,max:i}=e,s=Y1(t,(i-r)/2),a=(o,l)=>n&&o===0?0:o+l;return{min:a(r,-Math.abs(s)),max:a(i,s)}}function qn(e,t){return Object.assign(Object.create(e),t)}function Nu(e,t=[""],n,r,i=()=>e[0]){const s=n||e;typeof r>"u"&&(r=Sg("_fallback",e));const a={[Symbol.toStringTag]:"Object",_cacheable:!0,_scopes:e,_rootScopes:s,_fallback:r,_getTarget:i,override:o=>Nu([o,...e],t,s,r)};return new Proxy(a,{deleteProperty(o,l){return delete o[l],delete o._keys,delete e[0][l],!0},get(o,l){return _g(o,l,()=>Hb(l,t,e,o))},getOwnPropertyDescriptor(o,l){return Reflect.getOwnPropertyDescriptor(o._scopes[0],l)},getPrototypeOf(){return Reflect.getPrototypeOf(e[0])},has(o,l){return vh(o).includes(l)},ownKeys(o){return vh(o)},set(o,l,u){const d=o._storage||(o._storage=i());return o[l]=d[l]=u,delete o._keys,!0}})}function Dr(e,t,n,r){const i={_cacheable:!1,_proxy:e,_context:t,_subProxy:n,_stack:new Set,_descriptors:wg(e,r),setContext:s=>Dr(e,s,n,r),override:s=>Dr(e.override(s),t,n,r)};return new Proxy(i,{deleteProperty(s,a){return delete s[a],delete e[a],!0},get(s,a,o){return _g(s,a,()=>Ob(s,a,o))},getOwnPropertyDescriptor(s,a){return s._descriptors.allKeys?Reflect.has(e,a)?{enumerable:!0,configurable:!0}:void 0:Reflect.getOwnPropertyDescriptor(e,a)},getPrototypeOf(){return Reflect.getPrototypeOf(e)},has(s,a){return Reflect.has(e,a)},ownKeys(){return Reflect.ownKeys(e)},set(s,a,o){return e[a]=o,delete s[a],!0}})}function wg(e,t={scriptable:!0,indexable:!0}){const{_scriptable:n=t.scriptable,_indexable:r=t.indexable,_allKeys:i=t.allKeys}=e;return{allKeys:i,scriptable:n,indexable:r,isScriptable:vn(n)?n:()=>n,isIndexable:vn(r)?r:()=>r}}const Lb=(e,t)=>e?e+bu(t):t,Cu=(e,t)=>$(t)&&e!=="adapters"&&(Object.getPrototypeOf(t)===null||t.constructor===Object);function _g(e,t,n){if(Object.prototype.hasOwnProperty.call(e,t)||t==="constructor")return e[t];const r=n();return e[t]=r,r}function Ob(e,t,n){const{_proxy:r,_context:i,_subProxy:s,_descriptors:a}=e;let o=r[t];return vn(o)&&a.isScriptable(t)&&(o=Ab(t,o,e,n)),pe(o)&&o.length&&(o=Ib(t,o,e,a.isIndexable)),Cu(t,o)&&(o=Dr(o,i,s&&s[t],a)),o}function Ab(e,t,n,r){const{_proxy:i,_context:s,_subProxy:a,_stack:o}=n;if(o.has(e))throw new Error("Recursion detected: "+Array.from(o).join("->")+"->"+e);o.add(e);let l=t(s,a||r);return o.delete(e),Cu(e,l)&&(l=Mu(i._scopes,i,e,l)),l}function Ib(e,t,n,r){const{_proxy:i,_context:s,_subProxy:a,_descriptors:o}=n;if(typeof s.index<"u"&&r(e))return t[s.index%t.length];if($(t[0])){const l=t,u=i._scopes.filter(d=>d!==l);t=[];for(const d of l){const h=Mu(u,i,e,d);t.push(Dr(h,s,a&&a[e],o))}}return t}function jg(e,t,n){return vn(e)?e(t,n):e}const Fb=(e,t)=>e===!0?t:typeof e=="string"?Oa(t,e):void 0;function Bb(e,t,n,r,i){for(const s of t){const a=Fb(n,s);if(a){e.add(a);const o=jg(a._fallback,n,i);if(typeof o<"u"&&o!==n&&o!==r)return o}else if(a===!1&&typeof r<"u"&&n!==r)return null}return!1}function Mu(e,t,n,r){const i=t._rootScopes,s=jg(t._fallback,n,r),a=[...e,...i],o=new Set;o.add(r);let l=gh(o,a,n,s||n,r);return l===null||typeof s<"u"&&s!==n&&(l=gh(o,a,s,l,r),l===null)?!1:Nu(Array.from(o),[""],i,s,()=>$b(t,n,r))}function gh(e,t,n,r,i){for(;n;)n=Bb(e,t,n,r,i);return n}function $b(e,t,n){const r=e._getTarget();t in r||(r[t]={});const i=r[t];return pe(i)&&$(n)?n:i||{}}function Hb(e,t,n,r){let i;for(const s of t)if(i=Sg(Lb(s,e),n),typeof i<"u")return Cu(e,i)?Mu(n,r,e,i):i}function Sg(e,t){for(const n of t){if(!n)continue;const r=n[e];if(typeof r<"u")return r}}function vh(e){let t=e._keys;return t||(t=e._keys=Wb(e._scopes)),t}function Wb(e){const t=new Set;for(const n of e)for(const r of Object.keys(n).filter(i=>!i.startsWith("_")))t.add(r);return Array.from(t)}const Vb=Number.EPSILON||1e-14,Rr=(e,t)=>t<e.length&&!e[t].skip&&e[t],Ng=e=>e==="x"?"y":"x";function Ub(e,t,n,r){const i=e.skip?t:e,s=t,a=n.skip?t:n,o=ac(s,i),l=ac(a,s);let u=o/(o+l),d=l/(o+l);u=isNaN(u)?0:u,d=isNaN(d)?0:d;const h=r*u,f=r*d;return{previous:{x:s.x-h*(a.x-i.x),y:s.y-h*(a.y-i.y)},next:{x:s.x+f*(a.x-i.x),y:s.y+f*(a.y-i.y)}}}function Yb(e,t,n){const r=e.length;let i,s,a,o,l,u=Rr(e,0);for(let d=0;d<r-1;++d)if(l=u,u=Rr(e,d+1),!(!l||!u)){if(wi(t[d],0,Vb)){n[d]=n[d+1]=0;continue}i=n[d]/t[d],s=n[d+1]/t[d],o=Math.pow(i,2)+Math.pow(s,2),!(o<=9)&&(a=3/Math.sqrt(o),n[d]=i*a*t[d],n[d+1]=s*a*t[d])}}function Xb(e,t,n="x"){const r=Ng(n),i=e.length;let s,a,o,l=Rr(e,0);for(let u=0;u<i;++u){if(a=o,o=l,l=Rr(e,u+1),!o)continue;const d=o[n],h=o[r];a&&(s=(d-a[n])/3,o[`cp1${n}`]=d-s,o[`cp1${r}`]=h-s*t[u]),l&&(s=(l[n]-d)/3,o[`cp2${n}`]=d+s,o[`cp2${r}`]=h+s*t[u])}}function Kb(e,t="x"){const n=Ng(t),r=e.length,i=Array(r).fill(0),s=Array(r);let a,o,l,u=Rr(e,0);for(a=0;a<r;++a)if(o=l,l=u,u=Rr(e,a+1),!!l){if(u){const d=u[t]-l[t];i[a]=d!==0?(u[n]-l[n])/d:0}s[a]=o?u?zr(i[a-1])!==zr(i[a])?0:(i[a-1]+i[a])/2:i[a-1]:i[a]}Yb(e,i,s),Xb(e,s,t)}function Os(e,t,n){return Math.max(Math.min(e,n),t)}function Qb(e,t){let n,r,i,s,a,o=Zi(e[0],t);for(n=0,r=e.length;n<r;++n)a=s,s=o,o=n<r-1&&Zi(e[n+1],t),s&&(i=e[n],a&&(i.cp1x=Os(i.cp1x,t.left,t.right),i.cp1y=Os(i.cp1y,t.top,t.bottom)),o&&(i.cp2x=Os(i.cp2x,t.left,t.right),i.cp2y=Os(i.cp2y,t.top,t.bottom)))}function Gb(e,t,n,r,i){let s,a,o,l;if(t.spanGaps&&(e=e.filter(u=>!u.skip)),t.cubicInterpolationMode==="monotone")Kb(e,i);else{let u=r?e[e.length-1]:e[0];for(s=0,a=e.length;s<a;++s)o=e[s],l=Ub(u,o,e[Math.min(s+1,a-(r?0:1))%a],t.tension),o.cp1x=l.previous.x,o.cp1y=l.previous.y,o.cp2x=l.next.x,o.cp2y=l.next.y,u=o}t.capBezierPoints&&Qb(e,n)}function Pu(){return typeof window<"u"&&typeof document<"u"}function Eu(e){let t=e.parentNode;return t&&t.toString()==="[object ShadowRoot]"&&(t=t.host),t}function Ba(e,t,n){let r;return typeof e=="string"?(r=parseInt(e,10),e.indexOf("%")!==-1&&(r=r/100*t.parentNode[n])):r=e,r}const fo=e=>e.ownerDocument.defaultView.getComputedStyle(e,null);function Zb(e,t){return fo(e).getPropertyValue(t)}const qb=["top","right","bottom","left"];function $n(e,t,n){const r={};n=n?"-"+n:"";for(let i=0;i<4;i++){const s=qb[i];r[s]=parseFloat(e[t+"-"+s+n])||0}return r.width=r.left+r.right,r.height=r.top+r.bottom,r}const Jb=(e,t,n)=>(e>0||t>0)&&(!n||!n.shadowRoot);function ek(e,t){const n=e.touches,r=n&&n.length?n[0]:e,{offsetX:i,offsetY:s}=r;let a=!1,o,l;if(Jb(i,s,e.target))o=i,l=s;else{const u=t.getBoundingClientRect();o=r.clientX-u.left,l=r.clientY-u.top,a=!0}return{x:o,y:l,box:a}}function Cn(e,t){if("native"in e)return e;const{canvas:n,currentDevicePixelRatio:r}=t,i=fo(n),s=i.boxSizing==="border-box",a=$n(i,"padding"),o=$n(i,"border","width"),{x:l,y:u,box:d}=ek(e,n),h=a.left+(d&&o.left),f=a.top+(d&&o.top);let{width:p,height:m}=t;return s&&(p-=a.width+o.width,m-=a.height+o.height),{x:Math.round((l-h)/p*n.width/r),y:Math.round((u-f)/m*n.height/r)}}function tk(e,t,n){let r,i;if(t===void 0||n===void 0){const s=e&&Eu(e);if(!s)t=e.clientWidth,n=e.clientHeight;else{const a=s.getBoundingClientRect(),o=fo(s),l=$n(o,"border","width"),u=$n(o,"padding");t=a.width-u.width-l.width,n=a.height-u.height-l.height,r=Ba(o.maxWidth,s,"clientWidth"),i=Ba(o.maxHeight,s,"clientHeight")}}return{width:t,height:n,maxWidth:r||Ia,maxHeight:i||Ia}}const tn=e=>Math.round(e*10)/10;function nk(e,t,n,r){const i=fo(e),s=$n(i,"margin"),a=Ba(i.maxWidth,e,"clientWidth")||Ia,o=Ba(i.maxHeight,e,"clientHeight")||Ia,l=tk(e,t,n);let{width:u,height:d}=l;if(i.boxSizing==="content-box"){const f=$n(i,"border","width"),p=$n(i,"padding");u-=p.width+f.width,d-=p.height+f.height}return u=Math.max(0,u-s.width),d=Math.max(0,r?u/r:d-s.height),u=tn(Math.min(u,a,l.maxWidth)),d=tn(Math.min(d,o,l.maxHeight)),u&&!d&&(d=tn(u/2)),(t!==void 0||n!==void 0)&&r&&l.height&&d>l.height&&(d=l.height,u=tn(Math.floor(d*r))),{width:u,height:d}}function yh(e,t,n){const r=t||1,i=tn(e.height*r),s=tn(e.width*r);e.height=tn(e.height),e.width=tn(e.width);const a=e.canvas;return a.style&&(n||!a.style.height&&!a.style.width)&&(a.style.height=`${e.height}px`,a.style.width=`${e.width}px`),e.currentDevicePixelRatio!==r||a.height!==i||a.width!==s?(e.currentDevicePixelRatio=r,a.height=i,a.width=s,e.ctx.setTransform(r,0,0,r,0,0),!0):!1}const rk=function(){let e=!1;try{const t={get passive(){return e=!0,!1}};Pu()&&(window.addEventListener("test",null,t),window.removeEventListener("test",null,t))}catch{}return e}();function xh(e,t){const n=Zb(e,t),r=n&&n.match(/^(\d+)(\.\d+)?px$/);return r?+r[1]:void 0}function Mn(e,t,n,r){return{x:e.x+n*(t.x-e.x),y:e.y+n*(t.y-e.y)}}function ik(e,t,n,r){return{x:e.x+n*(t.x-e.x),y:r==="middle"?n<.5?e.y:t.y:r==="after"?n<1?e.y:t.y:n>0?t.y:e.y}}function sk(e,t,n,r){const i={x:e.cp2x,y:e.cp2y},s={x:t.cp1x,y:t.cp1y},a=Mn(e,i,n),o=Mn(i,s,n),l=Mn(s,t,n),u=Mn(a,o,n),d=Mn(o,l,n);return Mn(u,d,n)}const ak=function(e,t){return{x(n){return e+e+t-n},setWidth(n){t=n},textAlign(n){return n==="center"?n:n==="right"?"left":"right"},xPlus(n,r){return n-r},leftForLtr(n,r){return n-r}}},ok=function(){return{x(e){return e},setWidth(e){},textAlign(e){return e},xPlus(e,t){return e+t},leftForLtr(e,t){return e}}};function _r(e,t,n){return e?ak(t,n):ok()}function Cg(e,t){let n,r;(t==="ltr"||t==="rtl")&&(n=e.canvas.style,r=[n.getPropertyValue("direction"),n.getPropertyPriority("direction")],n.setProperty("direction",t,"important"),e.prevTextDirection=r)}function Mg(e,t){t!==void 0&&(delete e.prevTextDirection,e.canvas.style.setProperty("direction",t[0],t[1]))}function Pg(e){return e==="angle"?{between:ku,compare:sb,normalize:Qe}:{between:At,compare:(t,n)=>t-n,normalize:t=>t}}function bh({start:e,end:t,count:n,loop:r,style:i}){return{start:e%n,end:t%n,loop:r&&(t-e+1)%n===0,style:i}}function lk(e,t,n){const{property:r,start:i,end:s}=n,{between:a,normalize:o}=Pg(r),l=t.length;let{start:u,end:d,loop:h}=e,f,p;if(h){for(u+=l,d+=l,f=0,p=l;f<p&&a(o(t[u%l][r]),i,s);++f)u--,d--;u%=l,d%=l}return d<u&&(d+=l),{start:u,end:d,loop:h,style:e.style}}function Eg(e,t,n){if(!n)return[e];const{property:r,start:i,end:s}=n,a=t.length,{compare:o,between:l,normalize:u}=Pg(r),{start:d,end:h,loop:f,style:p}=lk(e,t,n),m=[];let v=!1,y=null,g,x,b;const k=()=>l(i,b,g)&&o(i,b)!==0,w=()=>o(s,g)===0||l(s,b,g),j=()=>v||k(),S=()=>!v||w();for(let N=d,T=d;N<=h;++N)x=t[N%a],!x.skip&&(g=u(x[r]),g!==b&&(v=l(g,i,s),y===null&&j()&&(y=o(g,i)===0?N:T),y!==null&&S()&&(m.push(bh({start:y,end:N,loop:f,count:a,style:p})),y=null),T=N,b=g));return y!==null&&m.push(bh({start:y,end:h,loop:f,count:a,style:p})),m}function Tg(e,t){const n=[],r=e.segments;for(let i=0;i<r.length;i++){const s=Eg(r[i],e.points,t);s.length&&n.push(...s)}return n}function ck(e,t,n,r){let i=0,s=t-1;if(n&&!r)for(;i<t&&!e[i].skip;)i++;for(;i<t&&e[i].skip;)i++;for(i%=t,n&&(s+=i);s>i&&e[s%t].skip;)s--;return s%=t,{start:i,end:s}}function uk(e,t,n,r){const i=e.length,s=[];let a=t,o=e[t],l;for(l=t+1;l<=n;++l){const u=e[l%i];u.skip||u.stop?o.skip||(r=!1,s.push({start:t%i,end:(l-1)%i,loop:r}),t=a=u.stop?l:null):(a=l,o.skip&&(t=l)),o=u}return a!==null&&s.push({start:t%i,end:a%i,loop:r}),s}function dk(e,t){const n=e.points,r=e.options.spanGaps,i=n.length;if(!i)return[];const s=!!e._loop,{start:a,end:o}=ck(n,i,s,r);if(r===!0)return kh(e,[{start:a,end:o,loop:s}],n,t);const l=o<a?o+i:o,u=!!e._fullLoop&&a===0&&o===i-1;return kh(e,uk(n,a,l,u),n,t)}function kh(e,t,n,r){return!r||!r.setContext||!n?t:hk(e,t,n,r)}function hk(e,t,n,r){const i=e._chart.getContext(),s=wh(e.options),{_datasetIndex:a,options:{spanGaps:o}}=e,l=n.length,u=[];let d=s,h=t[0].start,f=h;function p(m,v,y,g){const x=o?-1:1;if(m!==v){for(m+=l;n[m%l].skip;)m-=x;for(;n[v%l].skip;)v+=x;m%l!==v%l&&(u.push({start:m%l,end:v%l,loop:y,style:g}),d=g,h=v%l)}}for(const m of t){h=o?h:m.start;let v=n[h%l],y;for(f=h+1;f<=m.end;f++){const g=n[f%l];y=wh(r.setContext(qn(i,{type:"segment",p0:v,p1:g,p0DataIndex:(f-1)%l,p1DataIndex:f%l,datasetIndex:a}))),fk(y,d)&&p(h,f-1,m.loop,d),v=g,d=y}h<f-1&&p(h,f-1,m.loop,d)}return u}function wh(e){return{backgroundColor:e.backgroundColor,borderCapStyle:e.borderCapStyle,borderDash:e.borderDash,borderDashOffset:e.borderDashOffset,borderJoinStyle:e.borderJoinStyle,borderWidth:e.borderWidth,borderColor:e.borderColor}}function fk(e,t){if(!t)return!1;const n=[],r=function(i,s){return ju(s)?(n.includes(s)||n.push(s),n.indexOf(s)):s};return JSON.stringify(e,r)!==JSON.stringify(t,r)}function As(e,t,n){return e.options.clip?e[n]:t[n]}function pk(e,t){const{xScale:n,yScale:r}=e;return n&&r?{left:As(n,t,"left"),right:As(n,t,"right"),top:As(r,t,"top"),bottom:As(r,t,"bottom")}:t}function zg(e,t){const n=t._clip;if(n.disabled)return!1;const r=pk(t,e.chartArea);return{left:n.left===!1?0:r.left-(n.left===!0?0:n.left),right:n.right===!1?e.width:r.right+(n.right===!0?0:n.right),top:n.top===!1?0:r.top-(n.top===!0?0:n.top),bottom:n.bottom===!1?e.height:r.bottom+(n.bottom===!0?0:n.bottom)}}/*!
 * Chart.js v4.5.1
 * https://www.chartjs.org
 * (c) 2025 Chart.js Contributors
 * Released under the MIT License
 */class mk{constructor(){this._request=null,this._charts=new Map,this._running=!1,this._lastDate=void 0}_notify(t,n,r,i){const s=n.listeners[i],a=n.duration;s.forEach(o=>o({chart:t,initial:n.initial,numSteps:a,currentStep:Math.min(r-n.start,a)}))}_refresh(){this._request||(this._running=!0,this._request=gg.call(window,()=>{this._update(),this._request=null,this._running&&this._refresh()}))}_update(t=Date.now()){let n=0;this._charts.forEach((r,i)=>{if(!r.running||!r.items.length)return;const s=r.items;let a=s.length-1,o=!1,l;for(;a>=0;--a)l=s[a],l._active?(l._total>r.duration&&(r.duration=l._total),l.tick(t),o=!0):(s[a]=s[s.length-1],s.pop());o&&(i.draw(),this._notify(i,r,t,"progress")),s.length||(r.running=!1,this._notify(i,r,t,"complete"),r.initial=!1),n+=s.length}),this._lastDate=t,n===0&&(this._running=!1)}_getAnims(t){const n=this._charts;let r=n.get(t);return r||(r={running:!1,initial:!0,items:[],listeners:{complete:[],progress:[]}},n.set(t,r)),r}listen(t,n,r){this._getAnims(t).listeners[n].push(r)}add(t,n){!n||!n.length||this._getAnims(t).items.push(...n)}has(t){return this._getAnims(t).items.length>0}start(t){const n=this._charts.get(t);n&&(n.running=!0,n.start=Date.now(),n.duration=n.items.reduce((r,i)=>Math.max(r,i._duration),0),this._refresh())}running(t){if(!this._running)return!1;const n=this._charts.get(t);return!(!n||!n.running||!n.items.length)}stop(t){const n=this._charts.get(t);if(!n||!n.items.length)return;const r=n.items;let i=r.length-1;for(;i>=0;--i)r[i].cancel();n.items=[],this._notify(t,n,Date.now(),"complete")}remove(t){return this._charts.delete(t)}}var Et=new mk;const _h="transparent",gk={boolean(e,t,n){return n>.5?t:e},color(e,t,n){const r=hh(e||_h),i=r.valid&&hh(t||_h);return i&&i.valid?i.mix(r,n).hexString():t},number(e,t,n){return e+(t-e)*n}};class vk{constructor(t,n,r,i){const s=n[r];i=Ls([t.to,i,s,t.from]);const a=Ls([t.from,s,i]);this._active=!0,this._fn=t.fn||gk[t.type||typeof a],this._easing=_i[t.easing]||_i.linear,this._start=Math.floor(Date.now()+(t.delay||0)),this._duration=this._total=Math.floor(t.duration),this._loop=!!t.loop,this._target=n,this._prop=r,this._from=a,this._to=i,this._promises=void 0}active(){return this._active}update(t,n,r){if(this._active){this._notify(!1);const i=this._target[this._prop],s=r-this._start,a=this._duration-s;this._start=r,this._duration=Math.floor(Math.max(a,t.duration)),this._total+=s,this._loop=!!t.loop,this._to=Ls([t.to,n,i,t.from]),this._from=Ls([t.from,i,n])}}cancel(){this._active&&(this.tick(Date.now()),this._active=!1,this._notify(!1))}tick(t){const n=t-this._start,r=this._duration,i=this._prop,s=this._from,a=this._loop,o=this._to;let l;if(this._active=s!==o&&(a||n<r),!this._active){this._target[i]=o,this._notify(!0);return}if(n<0){this._target[i]=s;return}l=n/r%2,l=a&&l>1?2-l:l,l=this._easing(Math.min(1,Math.max(0,l))),this._target[i]=this._fn(s,o,l)}wait(){const t=this._promises||(this._promises=[]);return new Promise((n,r)=>{t.push({res:n,rej:r})})}_notify(t){const n=t?"res":"rej",r=this._promises||[];for(let i=0;i<r.length;i++)r[i][n]()}}class Dg{constructor(t,n){this._chart=t,this._properties=new Map,this.configure(n)}configure(t){if(!$(t))return;const n=Object.keys(ue.animation),r=this._properties;Object.getOwnPropertyNames(t).forEach(i=>{const s=t[i];if(!$(s))return;const a={};for(const o of n)a[o]=s[o];(pe(s.properties)&&s.properties||[i]).forEach(o=>{(o===i||!r.has(o))&&r.set(o,a)})})}_animateOptions(t,n){const r=n.options,i=xk(t,r);if(!i)return[];const s=this._createAnimations(i,r);return r.$shared&&yk(t.options.$animations,r).then(()=>{t.options=r},()=>{}),s}_createAnimations(t,n){const r=this._properties,i=[],s=t.$animations||(t.$animations={}),a=Object.keys(n),o=Date.now();let l;for(l=a.length-1;l>=0;--l){const u=a[l];if(u.charAt(0)==="$")continue;if(u==="options"){i.push(...this._animateOptions(t,n));continue}const d=n[u];let h=s[u];const f=r.get(u);if(h)if(f&&h.active()){h.update(f,d,o);continue}else h.cancel();if(!f||!f.duration){t[u]=d;continue}s[u]=h=new vk(f,t,u,d),i.push(h)}return i}update(t,n){if(this._properties.size===0){Object.assign(t,n);return}const r=this._createAnimations(t,n);if(r.length)return Et.add(this._chart,r),!0}}function yk(e,t){const n=[],r=Object.keys(t);for(let i=0;i<r.length;i++){const s=e[r[i]];s&&s.active()&&n.push(s.wait())}return Promise.all(n)}function xk(e,t){if(!t)return;let n=e.options;if(!n){e.options=t;return}return n.$shared&&(e.options=n=Object.assign({},n,{$shared:!1,$animations:{}})),n}function jh(e,t){const n=e&&e.options||{},r=n.reverse,i=n.min===void 0?t:0,s=n.max===void 0?t:0;return{start:r?s:i,end:r?i:s}}function bk(e,t,n){if(n===!1)return!1;const r=jh(e,n),i=jh(t,n);return{top:i.end,right:r.end,bottom:i.start,left:r.start}}function kk(e){let t,n,r,i;return $(e)?(t=e.top,n=e.right,r=e.bottom,i=e.left):t=n=r=i=e,{top:t,right:n,bottom:r,left:i,disabled:e===!1}}function Rg(e,t){const n=[],r=e._getSortedDatasetMetas(t);let i,s;for(i=0,s=r.length;i<s;++i)n.push(r[i].index);return n}function Sh(e,t,n,r={}){const i=e.keys,s=r.mode==="single";let a,o,l,u;if(t===null)return;let d=!1;for(a=0,o=i.length;a<o;++a){if(l=+i[a],l===n){if(d=!0,r.all)continue;break}u=e.values[l],De(u)&&(s||t===0||zr(t)===zr(u))&&(t+=u)}return!d&&!r.all?0:t}function wk(e,t){const{iScale:n,vScale:r}=t,i=n.axis==="x"?"x":"y",s=r.axis==="x"?"x":"y",a=Object.keys(e),o=new Array(a.length);let l,u,d;for(l=0,u=a.length;l<u;++l)d=a[l],o[l]={[i]:d,[s]:e[d]};return o}function Zo(e,t){const n=e&&e.options.stacked;return n||n===void 0&&t.stack!==void 0}function _k(e,t,n){return`${e.id}.${t.id}.${n.stack||n.type}`}function jk(e){const{min:t,max:n,minDefined:r,maxDefined:i}=e.getUserBounds();return{min:r?t:Number.NEGATIVE_INFINITY,max:i?n:Number.POSITIVE_INFINITY}}function Sk(e,t,n){const r=e[t]||(e[t]={});return r[n]||(r[n]={})}function Nh(e,t,n,r){for(const i of t.getMatchingVisibleMetas(r).reverse()){const s=e[i.index];if(n&&s>0||!n&&s<0)return i.index}return null}function Ch(e,t){const{chart:n,_cachedMeta:r}=e,i=n._stacks||(n._stacks={}),{iScale:s,vScale:a,index:o}=r,l=s.axis,u=a.axis,d=_k(s,a,r),h=t.length;let f;for(let p=0;p<h;++p){const m=t[p],{[l]:v,[u]:y}=m,g=m._stacks||(m._stacks={});f=g[u]=Sk(i,d,v),f[o]=y,f._top=Nh(f,a,!0,r.type),f._bottom=Nh(f,a,!1,r.type);const x=f._visualValues||(f._visualValues={});x[o]=y}}function qo(e,t){const n=e.scales;return Object.keys(n).filter(r=>n[r].axis===t).shift()}function Nk(e,t){return qn(e,{active:!1,dataset:void 0,datasetIndex:t,index:t,mode:"default",type:"dataset"})}function Ck(e,t,n){return qn(e,{active:!1,dataIndex:t,parsed:void 0,raw:void 0,element:n,index:t,mode:"default",type:"data"})}function qr(e,t){const n=e.controller.index,r=e.vScale&&e.vScale.axis;if(r){t=t||e._parsed;for(const i of t){const s=i._stacks;if(!s||s[r]===void 0||s[r][n]===void 0)return;delete s[r][n],s[r]._visualValues!==void 0&&s[r]._visualValues[n]!==void 0&&delete s[r]._visualValues[n]}}}const Jo=e=>e==="reset"||e==="none",Mh=(e,t)=>t?e:Object.assign({},e),Mk=(e,t,n)=>e&&!t.hidden&&t._stacked&&{keys:Rg(n,!0),values:null};class Si{constructor(t,n){this.chart=t,this._ctx=t.ctx,this.index=n,this._cachedDataOpts={},this._cachedMeta=this.getMeta(),this._type=this._cachedMeta.type,this.options=void 0,this._parsing=!1,this._data=void 0,this._objectData=void 0,this._sharedOptions=void 0,this._drawStart=void 0,this._drawCount=void 0,this.enableOptionSharing=!1,this.supportsDecimation=!1,this.$context=void 0,this._syncList=[],this.datasetElementType=new.target.datasetElementType,this.dataElementType=new.target.dataElementType,this.initialize()}initialize(){const t=this._cachedMeta;this.configure(),this.linkScales(),t._stacked=Zo(t.vScale,t),this.addElements(),this.options.fill&&!this.chart.isPluginEnabled("filler")&&console.warn("Tried to use the 'fill' option without the 'Filler' plugin enabled. Please import and register the 'Filler' plugin and make sure it is not disabled in the options")}updateIndex(t){this.index!==t&&qr(this._cachedMeta),this.index=t}linkScales(){const t=this.chart,n=this._cachedMeta,r=this.getDataset(),i=(h,f,p,m)=>h==="x"?f:h==="r"?m:p,s=n.xAxisID=B(r.xAxisID,qo(t,"x")),a=n.yAxisID=B(r.yAxisID,qo(t,"y")),o=n.rAxisID=B(r.rAxisID,qo(t,"r")),l=n.indexAxis,u=n.iAxisID=i(l,s,a,o),d=n.vAxisID=i(l,a,s,o);n.xScale=this.getScaleForId(s),n.yScale=this.getScaleForId(a),n.rScale=this.getScaleForId(o),n.iScale=this.getScaleForId(u),n.vScale=this.getScaleForId(d)}getDataset(){return this.chart.data.datasets[this.index]}getMeta(){return this.chart.getDatasetMeta(this.index)}getScaleForId(t){return this.chart.scales[t]}_getOtherScale(t){const n=this._cachedMeta;return t===n.iScale?n.vScale:n.iScale}reset(){this._update("reset")}_destroy(){const t=this._cachedMeta;this._data&&ch(this._data,this),t._stacked&&qr(t)}_dataCheck(){const t=this.getDataset(),n=t.data||(t.data=[]),r=this._data;if($(n)){const i=this._cachedMeta;this._data=wk(n,i)}else if(r!==n){if(r){ch(r,this);const i=this._cachedMeta;qr(i),i._parsed=[]}n&&Object.isExtensible(n)&&cb(n,this),this._syncList=[],this._data=n}}addElements(){const t=this._cachedMeta;this._dataCheck(),this.datasetElementType&&(t.dataset=new this.datasetElementType)}buildOrUpdateElements(t){const n=this._cachedMeta,r=this.getDataset();let i=!1;this._dataCheck();const s=n._stacked;n._stacked=Zo(n.vScale,n),n.stack!==r.stack&&(i=!0,qr(n),n.stack=r.stack),this._resyncElements(t),(i||s!==n._stacked)&&(Ch(this,n._parsed),n._stacked=Zo(n.vScale,n))}configure(){const t=this.chart.config,n=t.datasetScopeKeys(this._type),r=t.getOptionScopes(this.getDataset(),n,!0);this.options=t.createResolver(r,this.getContext()),this._parsing=this.options.parsing,this._cachedDataOpts={}}parse(t,n){const{_cachedMeta:r,_data:i}=this,{iScale:s,_stacked:a}=r,o=s.axis;let l=t===0&&n===i.length?!0:r._sorted,u=t>0&&r._parsed[t-1],d,h,f;if(this._parsing===!1)r._parsed=i,r._sorted=!0,f=i;else{pe(i[t])?f=this.parseArrayData(r,i,t,n):$(i[t])?f=this.parseObjectData(r,i,t,n):f=this.parsePrimitiveData(r,i,t,n);const p=()=>h[o]===null||u&&h[o]<u[o];for(d=0;d<n;++d)r._parsed[d+t]=h=f[d],l&&(p()&&(l=!1),u=h);r._sorted=l}a&&Ch(this,f)}parsePrimitiveData(t,n,r,i){const{iScale:s,vScale:a}=t,o=s.axis,l=a.axis,u=s.getLabels(),d=s===a,h=new Array(i);let f,p,m;for(f=0,p=i;f<p;++f)m=f+r,h[f]={[o]:d||s.parse(u[m],m),[l]:a.parse(n[m],m)};return h}parseArrayData(t,n,r,i){const{xScale:s,yScale:a}=t,o=new Array(i);let l,u,d,h;for(l=0,u=i;l<u;++l)d=l+r,h=n[d],o[l]={x:s.parse(h[0],d),y:a.parse(h[1],d)};return o}parseObjectData(t,n,r,i){const{xScale:s,yScale:a}=t,{xAxisKey:o="x",yAxisKey:l="y"}=this._parsing,u=new Array(i);let d,h,f,p;for(d=0,h=i;d<h;++d)f=d+r,p=n[f],u[d]={x:s.parse(Oa(p,o),f),y:a.parse(Oa(p,l),f)};return u}getParsed(t){return this._cachedMeta._parsed[t]}getDataElement(t){return this._cachedMeta.data[t]}applyStack(t,n,r){const i=this.chart,s=this._cachedMeta,a=n[t.axis],o={keys:Rg(i,!0),values:n._stacks[t.axis]._visualValues};return Sh(o,a,s.index,{mode:r})}updateRangeFromParsed(t,n,r,i){const s=r[n.axis];let a=s===null?NaN:s;const o=i&&r._stacks[n.axis];i&&o&&(i.values=o,a=Sh(i,s,this._cachedMeta.index)),t.min=Math.min(t.min,a),t.max=Math.max(t.max,a)}getMinMax(t,n){const r=this._cachedMeta,i=r._parsed,s=r._sorted&&t===r.iScale,a=i.length,o=this._getOtherScale(t),l=Mk(n,r,this.chart),u={min:Number.POSITIVE_INFINITY,max:Number.NEGATIVE_INFINITY},{min:d,max:h}=jk(o);let f,p;function m(){p=i[f];const v=p[o.axis];return!De(p[t.axis])||d>v||h<v}for(f=0;f<a&&!(!m()&&(this.updateRangeFromParsed(u,t,p,l),s));++f);if(s){for(f=a-1;f>=0;--f)if(!m()){this.updateRangeFromParsed(u,t,p,l);break}}return u}getAllParsedValues(t){const n=this._cachedMeta._parsed,r=[];let i,s,a;for(i=0,s=n.length;i<s;++i)a=n[i][t.axis],De(a)&&r.push(a);return r}getMaxOverflow(){return!1}getLabelAndValue(t){const n=this._cachedMeta,r=n.iScale,i=n.vScale,s=this.getParsed(t);return{label:r?""+r.getLabelForValue(s[r.axis]):"",value:i?""+i.getLabelForValue(s[i.axis]):""}}_update(t){const n=this._cachedMeta;this.update(t||"default"),n._clip=kk(B(this.options.clip,bk(n.xScale,n.yScale,this.getMaxOverflow())))}update(t){}draw(){const t=this._ctx,n=this.chart,r=this._cachedMeta,i=r.data||[],s=n.chartArea,a=[],o=this._drawStart||0,l=this._drawCount||i.length-o,u=this.options.drawActiveElementsOnTop;let d;for(r.dataset&&r.dataset.draw(t,s,o,l),d=o;d<o+l;++d){const h=i[d];h.hidden||(h.active&&u?a.push(h):h.draw(t,s))}for(d=0;d<a.length;++d)a[d].draw(t,s)}getStyle(t,n){const r=n?"active":"default";return t===void 0&&this._cachedMeta.dataset?this.resolveDatasetElementOptions(r):this.resolveDataElementOptions(t||0,r)}getContext(t,n,r){const i=this.getDataset();let s;if(t>=0&&t<this._cachedMeta.data.length){const a=this._cachedMeta.data[t];s=a.$context||(a.$context=Ck(this.getContext(),t,a)),s.parsed=this.getParsed(t),s.raw=i.data[t],s.index=s.dataIndex=t}else s=this.$context||(this.$context=Nk(this.chart.getContext(),this.index)),s.dataset=i,s.index=s.datasetIndex=this.index;return s.active=!!n,s.mode=r,s}resolveDatasetElementOptions(t){return this._resolveElementOptions(this.datasetElementType.id,t)}resolveDataElementOptions(t,n){return this._resolveElementOptions(this.dataElementType.id,n,t)}_resolveElementOptions(t,n="default",r){const i=n==="active",s=this._cachedDataOpts,a=t+"-"+n,o=s[a],l=this.enableOptionSharing&&Aa(r);if(o)return Mh(o,l);const u=this.chart.config,d=u.datasetElementScopeKeys(this._type,t),h=i?[`${t}Hover`,"hover",t,""]:[t,""],f=u.getOptionScopes(this.getDataset(),d),p=Object.keys(ue.elements[t]),m=()=>this.getContext(r,i,n),v=u.resolveNamedOptions(f,p,m,h);return v.$shared&&(v.$shared=l,s[a]=Object.freeze(Mh(v,l))),v}_resolveAnimations(t,n,r){const i=this.chart,s=this._cachedDataOpts,a=`animation-${n}`,o=s[a];if(o)return o;let l;if(i.options.animation!==!1){const d=this.chart.config,h=d.datasetAnimationScopeKeys(this._type,n),f=d.getOptionScopes(this.getDataset(),h);l=d.createResolver(f,this.getContext(t,r,n))}const u=new Dg(i,l&&l.animations);return l&&l._cacheable&&(s[a]=Object.freeze(u)),u}getSharedOptions(t){if(t.$shared)return this._sharedOptions||(this._sharedOptions=Object.assign({},t))}includeOptions(t,n){return!n||Jo(t)||this.chart._animationsDisabled}_getSharedOptions(t,n){const r=this.resolveDataElementOptions(t,n),i=this._sharedOptions,s=this.getSharedOptions(r),a=this.includeOptions(n,s)||s!==i;return this.updateSharedOptions(s,n,r),{sharedOptions:s,includeOptions:a}}updateElement(t,n,r,i){Jo(i)?Object.assign(t,r):this._resolveAnimations(n,i).update(t,r)}updateSharedOptions(t,n,r){t&&!Jo(n)&&this._resolveAnimations(void 0,n).update(t,r)}_setStyle(t,n,r,i){t.active=i;const s=this.getStyle(n,i);this._resolveAnimations(n,r,i).update(t,{options:!i&&this.getSharedOptions(s)||s})}removeHoverStyle(t,n,r){this._setStyle(t,r,"active",!1)}setHoverStyle(t,n,r){this._setStyle(t,r,"active",!0)}_removeDatasetHoverStyle(){const t=this._cachedMeta.dataset;t&&this._setStyle(t,void 0,"active",!1)}_setDatasetHoverStyle(){const t=this._cachedMeta.dataset;t&&this._setStyle(t,void 0,"active",!0)}_resyncElements(t){const n=this._data,r=this._cachedMeta.data;for(const[o,l,u]of this._syncList)this[o](l,u);this._syncList=[];const i=r.length,s=n.length,a=Math.min(s,i);a&&this.parse(0,a),s>i?this._insertElements(i,s-i,t):s<i&&this._removeElements(s,i-s)}_insertElements(t,n,r=!0){const i=this._cachedMeta,s=i.data,a=t+n;let o;const l=u=>{for(u.length+=n,o=u.length-1;o>=a;o--)u[o]=u[o-n]};for(l(s),o=t;o<a;++o)s[o]=new this.dataElementType;this._parsing&&l(i._parsed),this.parse(t,n),r&&this.updateElements(s,t,n,"reset")}updateElements(t,n,r,i){}_removeElements(t,n){const r=this._cachedMeta;if(this._parsing){const i=r._parsed.splice(t,n);r._stacked&&qr(r,i)}r.data.splice(t,n)}_sync(t){if(this._parsing)this._syncList.push(t);else{const[n,r,i]=t;this[n](r,i)}this.chart._dataChanges.push([this.index,...t])}_onDataPush(){const t=arguments.length;this._sync(["_insertElements",this.getDataset().data.length-t,t])}_onDataPop(){this._sync(["_removeElements",this._cachedMeta.data.length-1,1])}_onDataShift(){this._sync(["_removeElements",0,1])}_onDataSplice(t,n){n&&this._sync(["_removeElements",t,n]);const r=arguments.length-2;r&&this._sync(["_insertElements",t,r])}_onDataUnshift(){this._sync(["_insertElements",0,arguments.length])}}R(Si,"defaults",{}),R(Si,"datasetElementType",null),R(Si,"dataElementType",null);class ra extends Si{initialize(){this.enableOptionSharing=!0,this.supportsDecimation=!0,super.initialize()}update(t){const n=this._cachedMeta,{dataset:r,data:i=[],_dataset:s}=n,a=this.chart._animationsDisabled;let{start:o,count:l}=fb(n,i,a);this._drawStart=o,this._drawCount=l,pb(n)&&(o=0,l=i.length),r._chart=this.chart,r._datasetIndex=this.index,r._decimated=!!s._decimated,r.points=i;const u=this.resolveDatasetElementOptions(t);this.options.showLine||(u.borderWidth=0),u.segment=this.options.segment,this.updateElement(r,void 0,{animated:!a,options:u},t),this.updateElements(i,o,l,t)}updateElements(t,n,r,i){const s=i==="reset",{iScale:a,vScale:o,_stacked:l,_dataset:u}=this._cachedMeta,{sharedOptions:d,includeOptions:h}=this._getSharedOptions(n,i),f=a.axis,p=o.axis,{spanGaps:m,segment:v}=this.options,y=Gi(m)?m:Number.POSITIVE_INFINITY,g=this.chart._animationsDisabled||s||i==="none",x=n+r,b=t.length;let k=n>0&&this.getParsed(n-1);for(let w=0;w<b;++w){const j=t[w],S=g?j:{};if(w<n||w>=x){S.skip=!0;continue}const N=this.getParsed(w),T=Z(N[p]),E=S[f]=a.getPixelForValue(N[f],w),L=S[p]=s||T?o.getBasePixel():o.getPixelForValue(l?this.applyStack(o,N,l):N[p],w);S.skip=isNaN(E)||isNaN(L)||T,S.stop=w>0&&Math.abs(N[f]-k[f])>y,v&&(S.parsed=N,S.raw=u.data[w]),h&&(S.options=d||this.resolveDataElementOptions(w,j.active?"active":i)),g||this.updateElement(j,w,S,i),k=N}}getMaxOverflow(){const t=this._cachedMeta,n=t.dataset,r=n.options&&n.options.borderWidth||0,i=t.data||[];if(!i.length)return r;const s=i[0].size(this.resolveDataElementOptions(0)),a=i[i.length-1].size(this.resolveDataElementOptions(i.length-1));return Math.max(r,s,a)/2}draw(){const t=this._cachedMeta;t.dataset.updateControlPoints(this.chart.chartArea,t.iScale.axis),super.draw()}}R(ra,"id","line"),R(ra,"defaults",{datasetElementType:"line",dataElementType:"point",showLine:!0,spanGaps:!1}),R(ra,"overrides",{scales:{_index_:{type:"category"},_value_:{type:"linear"}}});function jn(){throw new Error("This method is not implemented: Check that a complete date adapter is provided.")}class Tu{constructor(t){R(this,"options");this.options=t||{}}static override(t){Object.assign(Tu.prototype,t)}init(){}formats(){return jn()}parse(){return jn()}format(){return jn()}add(){return jn()}diff(){return jn()}startOf(){return jn()}endOf(){return jn()}}var Pk={_date:Tu};function Ek(e,t,n,r){const{controller:i,data:s,_sorted:a}=e,o=i._cachedMeta.iScale,l=e.dataset&&e.dataset.options?e.dataset.options.spanGaps:null;if(o&&t===o.axis&&t!=="r"&&a&&s.length){const u=o._reversePixels?ob:Rn;if(r){if(i._sharedOptions){const d=s[0],h=typeof d.getRange=="function"&&d.getRange(t);if(h){const f=u(s,t,n-h),p=u(s,t,n+h);return{lo:f.lo,hi:p.hi}}}}else{const d=u(s,t,n);if(l){const{vScale:h}=i._cachedMeta,{_parsed:f}=e,p=f.slice(0,d.lo+1).reverse().findIndex(v=>!Z(v[h.axis]));d.lo-=Math.max(0,p);const m=f.slice(d.hi).findIndex(v=>!Z(v[h.axis]));d.hi+=Math.max(0,m)}return d}}return{lo:0,hi:s.length-1}}function po(e,t,n,r,i){const s=e.getSortedVisibleDatasetMetas(),a=n[t];for(let o=0,l=s.length;o<l;++o){const{index:u,data:d}=s[o],{lo:h,hi:f}=Ek(s[o],t,a,i);for(let p=h;p<=f;++p){const m=d[p];m.skip||r(m,u,p)}}}function Tk(e){const t=e.indexOf("x")!==-1,n=e.indexOf("y")!==-1;return function(r,i){const s=t?Math.abs(r.x-i.x):0,a=n?Math.abs(r.y-i.y):0;return Math.sqrt(Math.pow(s,2)+Math.pow(a,2))}}function el(e,t,n,r,i){const s=[];return!i&&!e.isPointInArea(t)||po(e,n,t,function(o,l,u){!i&&!Zi(o,e.chartArea,0)||o.inRange(t.x,t.y,r)&&s.push({element:o,datasetIndex:l,index:u})},!0),s}function zk(e,t,n,r){let i=[];function s(a,o,l){const{startAngle:u,endAngle:d}=a.getProps(["startAngle","endAngle"],r),{angle:h}=pg(a,{x:t.x,y:t.y});ku(h,u,d)&&i.push({element:a,datasetIndex:o,index:l})}return po(e,n,t,s),i}function Dk(e,t,n,r,i,s){let a=[];const o=Tk(n);let l=Number.POSITIVE_INFINITY;function u(d,h,f){const p=d.inRange(t.x,t.y,i);if(r&&!p)return;const m=d.getCenterPoint(i);if(!(!!s||e.isPointInArea(m))&&!p)return;const y=o(t,m);y<l?(a=[{element:d,datasetIndex:h,index:f}],l=y):y===l&&a.push({element:d,datasetIndex:h,index:f})}return po(e,n,t,u),a}function tl(e,t,n,r,i,s){return!s&&!e.isPointInArea(t)?[]:n==="r"&&!r?zk(e,t,n,i):Dk(e,t,n,r,i,s)}function Ph(e,t,n,r,i){const s=[],a=n==="x"?"inXRange":"inYRange";let o=!1;return po(e,n,t,(l,u,d)=>{l[a]&&l[a](t[n],i)&&(s.push({element:l,datasetIndex:u,index:d}),o=o||l.inRange(t.x,t.y,i))}),r&&!o?[]:s}var Rk={modes:{index(e,t,n,r){const i=Cn(t,e),s=n.axis||"x",a=n.includeInvisible||!1,o=n.intersect?el(e,i,s,r,a):tl(e,i,s,!1,r,a),l=[];return o.length?(e.getSortedVisibleDatasetMetas().forEach(u=>{const d=o[0].index,h=u.data[d];h&&!h.skip&&l.push({element:h,datasetIndex:u.index,index:d})}),l):[]},dataset(e,t,n,r){const i=Cn(t,e),s=n.axis||"xy",a=n.includeInvisible||!1;let o=n.intersect?el(e,i,s,r,a):tl(e,i,s,!1,r,a);if(o.length>0){const l=o[0].datasetIndex,u=e.getDatasetMeta(l).data;o=[];for(let d=0;d<u.length;++d)o.push({element:u[d],datasetIndex:l,index:d})}return o},point(e,t,n,r){const i=Cn(t,e),s=n.axis||"xy",a=n.includeInvisible||!1;return el(e,i,s,r,a)},nearest(e,t,n,r){const i=Cn(t,e),s=n.axis||"xy",a=n.includeInvisible||!1;return tl(e,i,s,n.intersect,r,a)},x(e,t,n,r){const i=Cn(t,e);return Ph(e,i,"x",n.intersect,r)},y(e,t,n,r){const i=Cn(t,e);return Ph(e,i,"y",n.intersect,r)}}};const Lg=["left","top","right","bottom"];function Jr(e,t){return e.filter(n=>n.pos===t)}function Eh(e,t){return e.filter(n=>Lg.indexOf(n.pos)===-1&&n.box.axis===t)}function ei(e,t){return e.sort((n,r)=>{const i=t?r:n,s=t?n:r;return i.weight===s.weight?i.index-s.index:i.weight-s.weight})}function Lk(e){const t=[];let n,r,i,s,a,o;for(n=0,r=(e||[]).length;n<r;++n)i=e[n],{position:s,options:{stack:a,stackWeight:o=1}}=i,t.push({index:n,box:i,pos:s,horizontal:i.isHorizontal(),weight:i.weight,stack:a&&s+a,stackWeight:o});return t}function Ok(e){const t={};for(const n of e){const{stack:r,pos:i,stackWeight:s}=n;if(!r||!Lg.includes(i))continue;const a=t[r]||(t[r]={count:0,placed:0,weight:0,size:0});a.count++,a.weight+=s}return t}function Ak(e,t){const n=Ok(e),{vBoxMaxWidth:r,hBoxMaxHeight:i}=t;let s,a,o;for(s=0,a=e.length;s<a;++s){o=e[s];const{fullSize:l}=o.box,u=n[o.stack],d=u&&o.stackWeight/u.weight;o.horizontal?(o.width=d?d*r:l&&t.availableWidth,o.height=i):(o.width=r,o.height=d?d*i:l&&t.availableHeight)}return n}function Ik(e){const t=Lk(e),n=ei(t.filter(u=>u.box.fullSize),!0),r=ei(Jr(t,"left"),!0),i=ei(Jr(t,"right")),s=ei(Jr(t,"top"),!0),a=ei(Jr(t,"bottom")),o=Eh(t,"x"),l=Eh(t,"y");return{fullSize:n,leftAndTop:r.concat(s),rightAndBottom:i.concat(l).concat(a).concat(o),chartArea:Jr(t,"chartArea"),vertical:r.concat(i).concat(l),horizontal:s.concat(a).concat(o)}}function Th(e,t,n,r){return Math.max(e[n],t[n])+Math.max(e[r],t[r])}function Og(e,t){e.top=Math.max(e.top,t.top),e.left=Math.max(e.left,t.left),e.bottom=Math.max(e.bottom,t.bottom),e.right=Math.max(e.right,t.right)}function Fk(e,t,n,r){const{pos:i,box:s}=n,a=e.maxPadding;if(!$(i)){n.size&&(e[i]-=n.size);const h=r[n.stack]||{size:0,count:1};h.size=Math.max(h.size,n.horizontal?s.height:s.width),n.size=h.size/h.count,e[i]+=n.size}s.getPadding&&Og(a,s.getPadding());const o=Math.max(0,t.outerWidth-Th(a,e,"left","right")),l=Math.max(0,t.outerHeight-Th(a,e,"top","bottom")),u=o!==e.w,d=l!==e.h;return e.w=o,e.h=l,n.horizontal?{same:u,other:d}:{same:d,other:u}}function Bk(e){const t=e.maxPadding;function n(r){const i=Math.max(t[r]-e[r],0);return e[r]+=i,i}e.y+=n("top"),e.x+=n("left"),n("right"),n("bottom")}function $k(e,t){const n=t.maxPadding;function r(i){const s={left:0,top:0,right:0,bottom:0};return i.forEach(a=>{s[a]=Math.max(t[a],n[a])}),s}return r(e?["left","right"]:["top","bottom"])}function ci(e,t,n,r){const i=[];let s,a,o,l,u,d;for(s=0,a=e.length,u=0;s<a;++s){o=e[s],l=o.box,l.update(o.width||t.w,o.height||t.h,$k(o.horizontal,t));const{same:h,other:f}=Fk(t,n,o,r);u|=h&&i.length,d=d||f,l.fullSize||i.push(o)}return u&&ci(i,t,n,r)||d}function Is(e,t,n,r,i){e.top=n,e.left=t,e.right=t+r,e.bottom=n+i,e.width=r,e.height=i}function zh(e,t,n,r){const i=n.padding;let{x:s,y:a}=t;for(const o of e){const l=o.box,u=r[o.stack]||{placed:0,weight:1},d=o.stackWeight/u.weight||1;if(o.horizontal){const h=t.w*d,f=u.size||l.height;Aa(u.start)&&(a=u.start),l.fullSize?Is(l,i.left,a,n.outerWidth-i.right-i.left,f):Is(l,t.left+u.placed,a,h,f),u.start=a,u.placed+=h,a=l.bottom}else{const h=t.h*d,f=u.size||l.width;Aa(u.start)&&(s=u.start),l.fullSize?Is(l,s,i.top,f,n.outerHeight-i.bottom-i.top):Is(l,s,t.top+u.placed,f,h),u.start=s,u.placed+=h,s=l.right}}t.x=s,t.y=a}var st={addBox(e,t){e.boxes||(e.boxes=[]),t.fullSize=t.fullSize||!1,t.position=t.position||"top",t.weight=t.weight||0,t._layers=t._layers||function(){return[{z:0,draw(n){t.draw(n)}}]},e.boxes.push(t)},removeBox(e,t){const n=e.boxes?e.boxes.indexOf(t):-1;n!==-1&&e.boxes.splice(n,1)},configure(e,t,n){t.fullSize=n.fullSize,t.position=n.position,t.weight=n.weight},update(e,t,n,r){if(!e)return;const i=ct(e.options.layout.padding),s=Math.max(t-i.width,0),a=Math.max(n-i.height,0),o=Ik(e.boxes),l=o.vertical,u=o.horizontal;Y(e.boxes,v=>{typeof v.beforeLayout=="function"&&v.beforeLayout()});const d=l.reduce((v,y)=>y.box.options&&y.box.options.display===!1?v:v+1,0)||1,h=Object.freeze({outerWidth:t,outerHeight:n,padding:i,availableWidth:s,availableHeight:a,vBoxMaxWidth:s/2/d,hBoxMaxHeight:a/2}),f=Object.assign({},i);Og(f,ct(r));const p=Object.assign({maxPadding:f,w:s,h:a,x:i.left,y:i.top},i),m=Ak(l.concat(u),h);ci(o.fullSize,p,h,m),ci(l,p,h,m),ci(u,p,h,m)&&ci(l,p,h,m),Bk(p),zh(o.leftAndTop,p,h,m),p.x+=p.w,p.y+=p.h,zh(o.rightAndBottom,p,h,m),e.chartArea={left:p.left,top:p.top,right:p.left+p.w,bottom:p.top+p.h,height:p.h,width:p.w},Y(o.chartArea,v=>{const y=v.box;Object.assign(y,e.chartArea),y.update(p.w,p.h,{left:0,top:0,right:0,bottom:0})})}};class Ag{acquireContext(t,n){}releaseContext(t){return!1}addEventListener(t,n,r){}removeEventListener(t,n,r){}getDevicePixelRatio(){return 1}getMaximumSize(t,n,r,i){return n=Math.max(0,n||t.width),r=r||t.height,{width:n,height:Math.max(0,i?Math.floor(n/i):r)}}isAttached(t){return!0}updateConfig(t){}}class Hk extends Ag{acquireContext(t){return t&&t.getContext&&t.getContext("2d")||null}updateConfig(t){t.options.animation=!1}}const ia="$chartjs",Wk={touchstart:"mousedown",touchmove:"mousemove",touchend:"mouseup",pointerenter:"mouseenter",pointerdown:"mousedown",pointermove:"mousemove",pointerup:"mouseup",pointerleave:"mouseout",pointerout:"mouseout"},Dh=e=>e===null||e==="";function Vk(e,t){const n=e.style,r=e.getAttribute("height"),i=e.getAttribute("width");if(e[ia]={initial:{height:r,width:i,style:{display:n.display,height:n.height,width:n.width}}},n.display=n.display||"block",n.boxSizing=n.boxSizing||"border-box",Dh(i)){const s=xh(e,"width");s!==void 0&&(e.width=s)}if(Dh(r))if(e.style.height==="")e.height=e.width/(t||2);else{const s=xh(e,"height");s!==void 0&&(e.height=s)}return e}const Ig=rk?{passive:!0}:!1;function Uk(e,t,n){e&&e.addEventListener(t,n,Ig)}function Yk(e,t,n){e&&e.canvas&&e.canvas.removeEventListener(t,n,Ig)}function Xk(e,t){const n=Wk[e.type]||e.type,{x:r,y:i}=Cn(e,t);return{type:n,chart:t,native:e,x:r!==void 0?r:null,y:i!==void 0?i:null}}function $a(e,t){for(const n of e)if(n===t||n.contains(t))return!0}function Kk(e,t,n){const r=e.canvas,i=new MutationObserver(s=>{let a=!1;for(const o of s)a=a||$a(o.addedNodes,r),a=a&&!$a(o.removedNodes,r);a&&n()});return i.observe(document,{childList:!0,subtree:!0}),i}function Qk(e,t,n){const r=e.canvas,i=new MutationObserver(s=>{let a=!1;for(const o of s)a=a||$a(o.removedNodes,r),a=a&&!$a(o.addedNodes,r);a&&n()});return i.observe(document,{childList:!0,subtree:!0}),i}const Ji=new Map;let Rh=0;function Fg(){const e=window.devicePixelRatio;e!==Rh&&(Rh=e,Ji.forEach((t,n)=>{n.currentDevicePixelRatio!==e&&t()}))}function Gk(e,t){Ji.size||window.addEventListener("resize",Fg),Ji.set(e,t)}function Zk(e){Ji.delete(e),Ji.size||window.removeEventListener("resize",Fg)}function qk(e,t,n){const r=e.canvas,i=r&&Eu(r);if(!i)return;const s=vg((o,l)=>{const u=i.clientWidth;n(o,l),u<i.clientWidth&&n()},window),a=new ResizeObserver(o=>{const l=o[0],u=l.contentRect.width,d=l.contentRect.height;u===0&&d===0||s(u,d)});return a.observe(i),Gk(e,s),a}function nl(e,t,n){n&&n.disconnect(),t==="resize"&&Zk(e)}function Jk(e,t,n){const r=e.canvas,i=vg(s=>{e.ctx!==null&&n(Xk(s,e))},e);return Uk(r,t,i),i}class ew extends Ag{acquireContext(t,n){const r=t&&t.getContext&&t.getContext("2d");return r&&r.canvas===t?(Vk(t,n),r):null}releaseContext(t){const n=t.canvas;if(!n[ia])return!1;const r=n[ia].initial;["height","width"].forEach(s=>{const a=r[s];Z(a)?n.removeAttribute(s):n.setAttribute(s,a)});const i=r.style||{};return Object.keys(i).forEach(s=>{n.style[s]=i[s]}),n.width=n.width,delete n[ia],!0}addEventListener(t,n,r){this.removeEventListener(t,n);const i=t.$proxies||(t.$proxies={}),a={attach:Kk,detach:Qk,resize:qk}[n]||Jk;i[n]=a(t,n,r)}removeEventListener(t,n){const r=t.$proxies||(t.$proxies={}),i=r[n];if(!i)return;({attach:nl,detach:nl,resize:nl}[n]||Yk)(t,n,i),r[n]=void 0}getDevicePixelRatio(){return window.devicePixelRatio}getMaximumSize(t,n,r,i){return nk(t,n,r,i)}isAttached(t){const n=t&&Eu(t);return!!(n&&n.isConnected)}}function tw(e){return!Pu()||typeof OffscreenCanvas<"u"&&e instanceof OffscreenCanvas?Hk:ew}class vt{constructor(){R(this,"x");R(this,"y");R(this,"active",!1);R(this,"options");R(this,"$animations")}tooltipPosition(t){const{x:n,y:r}=this.getProps(["x","y"],t);return{x:n,y:r}}hasValue(){return Gi(this.x)&&Gi(this.y)}getProps(t,n){const r=this.$animations;if(!n||!r)return this;const i={};return t.forEach(s=>{i[s]=r[s]&&r[s].active()?r[s]._to:this[s]}),i}}R(vt,"defaults",{}),R(vt,"defaultRoutes");function nw(e,t){const n=e.options.ticks,r=rw(e),i=Math.min(n.maxTicksLimit||r,r),s=n.major.enabled?sw(t):[],a=s.length,o=s[0],l=s[a-1],u=[];if(a>i)return aw(t,u,s,a/i),u;const d=iw(s,t,i);if(a>0){let h,f;const p=a>1?Math.round((l-o)/(a-1)):null;for(Fs(t,u,d,Z(p)?0:o-p,o),h=0,f=a-1;h<f;h++)Fs(t,u,d,s[h],s[h+1]);return Fs(t,u,d,l,Z(p)?t.length:l+p),u}return Fs(t,u,d),u}function rw(e){const t=e.options.offset,n=e._tickSize(),r=e._length/n+(t?0:1),i=e._maxLength/n;return Math.floor(Math.min(r,i))}function iw(e,t,n){const r=ow(e),i=t.length/n;if(!r)return Math.max(i,1);const s=eb(r);for(let a=0,o=s.length-1;a<o;a++){const l=s[a];if(l>i)return l}return Math.max(i,1)}function sw(e){const t=[];let n,r;for(n=0,r=e.length;n<r;n++)e[n].major&&t.push(n);return t}function aw(e,t,n,r){let i=0,s=n[0],a;for(r=Math.ceil(r),a=0;a<e.length;a++)a===s&&(t.push(e[a]),i++,s=n[i*r])}function Fs(e,t,n,r,i){const s=B(r,0),a=Math.min(B(i,e.length),e.length);let o=0,l,u,d;for(n=Math.ceil(n),i&&(l=i-r,n=l/Math.floor(l/n)),d=s;d<0;)o++,d=Math.round(s+o*n);for(u=Math.max(s,0);u<a;u++)u===d&&(t.push(e[u]),o++,d=Math.round(s+o*n))}function ow(e){const t=e.length;let n,r;if(t<2)return!1;for(r=e[0],n=1;n<t;++n)if(e[n]-e[n-1]!==r)return!1;return r}const lw=e=>e==="left"?"right":e==="right"?"left":e,Lh=(e,t,n)=>t==="top"||t==="left"?e[t]+n:e[t]-n,Oh=(e,t)=>Math.min(t||e,e);function Ah(e,t){const n=[],r=e.length/t,i=e.length;let s=0;for(;s<i;s+=r)n.push(e[Math.floor(s)]);return n}function cw(e,t,n){const r=e.ticks.length,i=Math.min(t,r-1),s=e._startPixel,a=e._endPixel,o=1e-6;let l=e.getPixelForTick(i),u;if(!(n&&(r===1?u=Math.max(l-s,a-l):t===0?u=(e.getPixelForTick(1)-l)/2:u=(l-e.getPixelForTick(i-1))/2,l+=i<t?u:-u,l<s-o||l>a+o)))return l}function uw(e,t){Y(e,n=>{const r=n.gc,i=r.length/2;let s;if(i>t){for(s=0;s<i;++s)delete n.data[r[s]];r.splice(0,i)}})}function ti(e){return e.drawTicks?e.tickLength:0}function Ih(e,t){if(!e.display)return 0;const n=Ee(e.font,t),r=ct(e.padding);return(pe(e.text)?e.text.length:1)*n.lineHeight+r.height}function dw(e,t){return qn(e,{scale:t,type:"scale"})}function hw(e,t,n){return qn(e,{tick:n,index:t,type:"tick"})}function fw(e,t,n){let r=_u(e);return(n&&t!=="right"||!n&&t==="right")&&(r=lw(r)),r}function pw(e,t,n,r){const{top:i,left:s,bottom:a,right:o,chart:l}=e,{chartArea:u,scales:d}=l;let h=0,f,p,m;const v=a-i,y=o-s;if(e.isHorizontal()){if(p=Ce(r,s,o),$(n)){const g=Object.keys(n)[0],x=n[g];m=d[g].getPixelForValue(x)+v-t}else n==="center"?m=(u.bottom+u.top)/2+v-t:m=Lh(e,n,t);f=o-s}else{if($(n)){const g=Object.keys(n)[0],x=n[g];p=d[g].getPixelForValue(x)-y+t}else n==="center"?p=(u.left+u.right)/2-y+t:p=Lh(e,n,t);m=Ce(r,a,i),h=n==="left"?-we:we}return{titleX:p,titleY:m,maxWidth:f,rotation:h}}class Hr extends vt{constructor(t){super(),this.id=t.id,this.type=t.type,this.options=void 0,this.ctx=t.ctx,this.chart=t.chart,this.top=void 0,this.bottom=void 0,this.left=void 0,this.right=void 0,this.width=void 0,this.height=void 0,this._margins={left:0,right:0,top:0,bottom:0},this.maxWidth=void 0,this.maxHeight=void 0,this.paddingTop=void 0,this.paddingBottom=void 0,this.paddingLeft=void 0,this.paddingRight=void 0,this.axis=void 0,this.labelRotation=void 0,this.min=void 0,this.max=void 0,this._range=void 0,this.ticks=[],this._gridLineItems=null,this._labelItems=null,this._labelSizes=null,this._length=0,this._maxLength=0,this._longestTextCache={},this._startPixel=void 0,this._endPixel=void 0,this._reversePixels=!1,this._userMax=void 0,this._userMin=void 0,this._suggestedMax=void 0,this._suggestedMin=void 0,this._ticksLength=0,this._borderValue=0,this._cache={},this._dataLimitsCached=!1,this.$context=void 0}init(t){this.options=t.setContext(this.getContext()),this.axis=t.axis,this._userMin=this.parse(t.min),this._userMax=this.parse(t.max),this._suggestedMin=this.parse(t.suggestedMin),this._suggestedMax=this.parse(t.suggestedMax)}parse(t,n){return t}getUserBounds(){let{_userMin:t,_userMax:n,_suggestedMin:r,_suggestedMax:i}=this;return t=bt(t,Number.POSITIVE_INFINITY),n=bt(n,Number.NEGATIVE_INFINITY),r=bt(r,Number.POSITIVE_INFINITY),i=bt(i,Number.NEGATIVE_INFINITY),{min:bt(t,r),max:bt(n,i),minDefined:De(t),maxDefined:De(n)}}getMinMax(t){let{min:n,max:r,minDefined:i,maxDefined:s}=this.getUserBounds(),a;if(i&&s)return{min:n,max:r};const o=this.getMatchingVisibleMetas();for(let l=0,u=o.length;l<u;++l)a=o[l].controller.getMinMax(this,t),i||(n=Math.min(n,a.min)),s||(r=Math.max(r,a.max));return n=s&&n>r?r:n,r=i&&n>r?n:r,{min:bt(n,bt(r,n)),max:bt(r,bt(n,r))}}getPadding(){return{left:this.paddingLeft||0,top:this.paddingTop||0,right:this.paddingRight||0,bottom:this.paddingBottom||0}}getTicks(){return this.ticks}getLabels(){const t=this.chart.data;return this.options.labels||(this.isHorizontal()?t.xLabels:t.yLabels)||t.labels||[]}getLabelItems(t=this.chart.chartArea){return this._labelItems||(this._labelItems=this._computeLabelItems(t))}beforeLayout(){this._cache={},this._dataLimitsCached=!1}beforeUpdate(){te(this.options.beforeUpdate,[this])}update(t,n,r){const{beginAtZero:i,grace:s,ticks:a}=this.options,o=a.sampleSize;this.beforeUpdate(),this.maxWidth=t,this.maxHeight=n,this._margins=r=Object.assign({left:0,right:0,top:0,bottom:0},r),this.ticks=null,this._labelSizes=null,this._gridLineItems=null,this._labelItems=null,this.beforeSetDimensions(),this.setDimensions(),this.afterSetDimensions(),this._maxLength=this.isHorizontal()?this.width+r.left+r.right:this.height+r.top+r.bottom,this._dataLimitsCached||(this.beforeDataLimits(),this.determineDataLimits(),this.afterDataLimits(),this._range=Rb(this,s,i),this._dataLimitsCached=!0),this.beforeBuildTicks(),this.ticks=this.buildTicks()||[],this.afterBuildTicks();const l=o<this.ticks.length;this._convertTicksToLabels(l?Ah(this.ticks,o):this.ticks),this.configure(),this.beforeCalculateLabelRotation(),this.calculateLabelRotation(),this.afterCalculateLabelRotation(),a.display&&(a.autoSkip||a.source==="auto")&&(this.ticks=nw(this,this.ticks),this._labelSizes=null,this.afterAutoSkip()),l&&this._convertTicksToLabels(this.ticks),this.beforeFit(),this.fit(),this.afterFit(),this.afterUpdate()}configure(){let t=this.options.reverse,n,r;this.isHorizontal()?(n=this.left,r=this.right):(n=this.top,r=this.bottom,t=!t),this._startPixel=n,this._endPixel=r,this._reversePixels=t,this._length=r-n,this._alignToPixels=this.options.alignToPixels}afterUpdate(){te(this.options.afterUpdate,[this])}beforeSetDimensions(){te(this.options.beforeSetDimensions,[this])}setDimensions(){this.isHorizontal()?(this.width=this.maxWidth,this.left=0,this.right=this.width):(this.height=this.maxHeight,this.top=0,this.bottom=this.height),this.paddingLeft=0,this.paddingTop=0,this.paddingRight=0,this.paddingBottom=0}afterSetDimensions(){te(this.options.afterSetDimensions,[this])}_callHooks(t){this.chart.notifyPlugins(t,this.getContext()),te(this.options[t],[this])}beforeDataLimits(){this._callHooks("beforeDataLimits")}determineDataLimits(){}afterDataLimits(){this._callHooks("afterDataLimits")}beforeBuildTicks(){this._callHooks("beforeBuildTicks")}buildTicks(){return[]}afterBuildTicks(){this._callHooks("afterBuildTicks")}beforeTickToLabelConversion(){te(this.options.beforeTickToLabelConversion,[this])}generateTickLabels(t){const n=this.options.ticks;let r,i,s;for(r=0,i=t.length;r<i;r++)s=t[r],s.label=te(n.callback,[s.value,r,t],this)}afterTickToLabelConversion(){te(this.options.afterTickToLabelConversion,[this])}beforeCalculateLabelRotation(){te(this.options.beforeCalculateLabelRotation,[this])}calculateLabelRotation(){const t=this.options,n=t.ticks,r=Oh(this.ticks.length,t.ticks.maxTicksLimit),i=n.minRotation||0,s=n.maxRotation;let a=i,o,l,u;if(!this._isVisible()||!n.display||i>=s||r<=1||!this.isHorizontal()){this.labelRotation=i;return}const d=this._getLabelSizes(),h=d.widest.width,f=d.highest.height,p=Pe(this.chart.width-h,0,this.maxWidth);o=t.offset?this.maxWidth/r:p/(r-1),h+6>o&&(o=p/(r-(t.offset?.5:1)),l=this.maxHeight-ti(t.grid)-n.padding-Ih(t.title,this.chart.options.font),u=Math.sqrt(h*h+f*f),a=ib(Math.min(Math.asin(Pe((d.highest.height+6)/o,-1,1)),Math.asin(Pe(l/u,-1,1))-Math.asin(Pe(f/u,-1,1)))),a=Math.max(i,Math.min(s,a))),this.labelRotation=a}afterCalculateLabelRotation(){te(this.options.afterCalculateLabelRotation,[this])}afterAutoSkip(){}beforeFit(){te(this.options.beforeFit,[this])}fit(){const t={width:0,height:0},{chart:n,options:{ticks:r,title:i,grid:s}}=this,a=this._isVisible(),o=this.isHorizontal();if(a){const l=Ih(i,n.options.font);if(o?(t.width=this.maxWidth,t.height=ti(s)+l):(t.height=this.maxHeight,t.width=ti(s)+l),r.display&&this.ticks.length){const{first:u,last:d,widest:h,highest:f}=this._getLabelSizes(),p=r.padding*2,m=Dn(this.labelRotation),v=Math.cos(m),y=Math.sin(m);if(o){const g=r.mirror?0:y*h.width+v*f.height;t.height=Math.min(this.maxHeight,t.height+g+p)}else{const g=r.mirror?0:v*h.width+y*f.height;t.width=Math.min(this.maxWidth,t.width+g+p)}this._calculatePadding(u,d,y,v)}}this._handleMargins(),o?(this.width=this._length=n.width-this._margins.left-this._margins.right,this.height=t.height):(this.width=t.width,this.height=this._length=n.height-this._margins.top-this._margins.bottom)}_calculatePadding(t,n,r,i){const{ticks:{align:s,padding:a},position:o}=this.options,l=this.labelRotation!==0,u=o!=="top"&&this.axis==="x";if(this.isHorizontal()){const d=this.getPixelForTick(0)-this.left,h=this.right-this.getPixelForTick(this.ticks.length-1);let f=0,p=0;l?u?(f=i*t.width,p=r*n.height):(f=r*t.height,p=i*n.width):s==="start"?p=n.width:s==="end"?f=t.width:s!=="inner"&&(f=t.width/2,p=n.width/2),this.paddingLeft=Math.max((f-d+a)*this.width/(this.width-d),0),this.paddingRight=Math.max((p-h+a)*this.width/(this.width-h),0)}else{let d=n.height/2,h=t.height/2;s==="start"?(d=0,h=t.height):s==="end"&&(d=n.height,h=0),this.paddingTop=d+a,this.paddingBottom=h+a}}_handleMargins(){this._margins&&(this._margins.left=Math.max(this.paddingLeft,this._margins.left),this._margins.top=Math.max(this.paddingTop,this._margins.top),this._margins.right=Math.max(this.paddingRight,this._margins.right),this._margins.bottom=Math.max(this.paddingBottom,this._margins.bottom))}afterFit(){te(this.options.afterFit,[this])}isHorizontal(){const{axis:t,position:n}=this.options;return n==="top"||n==="bottom"||t==="x"}isFullSize(){return this.options.fullSize}_convertTicksToLabels(t){this.beforeTickToLabelConversion(),this.generateTickLabels(t);let n,r;for(n=0,r=t.length;n<r;n++)Z(t[n].label)&&(t.splice(n,1),r--,n--);this.afterTickToLabelConversion()}_getLabelSizes(){let t=this._labelSizes;if(!t){const n=this.options.ticks.sampleSize;let r=this.ticks;n<r.length&&(r=Ah(r,n)),this._labelSizes=t=this._computeLabelSizes(r,r.length,this.options.ticks.maxTicksLimit)}return t}_computeLabelSizes(t,n,r){const{ctx:i,_longestTextCache:s}=this,a=[],o=[],l=Math.floor(n/Oh(n,r));let u=0,d=0,h,f,p,m,v,y,g,x,b,k,w;for(h=0;h<n;h+=l){if(m=t[h].label,v=this._resolveTickFontOptions(h),i.font=y=v.string,g=s[y]=s[y]||{data:{},gc:[]},x=v.lineHeight,b=k=0,!Z(m)&&!pe(m))b=ph(i,g.data,g.gc,b,m),k=x;else if(pe(m))for(f=0,p=m.length;f<p;++f)w=m[f],!Z(w)&&!pe(w)&&(b=ph(i,g.data,g.gc,b,w),k+=x);a.push(b),o.push(k),u=Math.max(b,u),d=Math.max(k,d)}uw(s,n);const j=a.indexOf(u),S=o.indexOf(d),N=T=>({width:a[T]||0,height:o[T]||0});return{first:N(0),last:N(n-1),widest:N(j),highest:N(S),widths:a,heights:o}}getLabelForValue(t){return t}getPixelForValue(t,n){return NaN}getValueForPixel(t){}getPixelForTick(t){const n=this.ticks;return t<0||t>n.length-1?null:this.getPixelForValue(n[t].value)}getPixelForDecimal(t){this._reversePixels&&(t=1-t);const n=this._startPixel+t*this._length;return ab(this._alignToPixels?_n(this.chart,n,0):n)}getDecimalForPixel(t){const n=(t-this._startPixel)/this._length;return this._reversePixels?1-n:n}getBasePixel(){return this.getPixelForValue(this.getBaseValue())}getBaseValue(){const{min:t,max:n}=this;return t<0&&n<0?n:t>0&&n>0?t:0}getContext(t){const n=this.ticks||[];if(t>=0&&t<n.length){const r=n[t];return r.$context||(r.$context=hw(this.getContext(),t,r))}return this.$context||(this.$context=dw(this.chart.getContext(),this))}_tickSize(){const t=this.options.ticks,n=Dn(this.labelRotation),r=Math.abs(Math.cos(n)),i=Math.abs(Math.sin(n)),s=this._getLabelSizes(),a=t.autoSkipPadding||0,o=s?s.widest.width+a:0,l=s?s.highest.height+a:0;return this.isHorizontal()?l*r>o*i?o/r:l/i:l*i<o*r?l/r:o/i}_isVisible(){const t=this.options.display;return t!=="auto"?!!t:this.getMatchingVisibleMetas().length>0}_computeGridLineItems(t){const n=this.axis,r=this.chart,i=this.options,{grid:s,position:a,border:o}=i,l=s.offset,u=this.isHorizontal(),h=this.ticks.length+(l?1:0),f=ti(s),p=[],m=o.setContext(this.getContext()),v=m.display?m.width:0,y=v/2,g=function(U){return _n(r,U,v)};let x,b,k,w,j,S,N,T,E,L,A,q;if(a==="top")x=g(this.bottom),S=this.bottom-f,T=x-y,L=g(t.top)+y,q=t.bottom;else if(a==="bottom")x=g(this.top),L=t.top,q=g(t.bottom)-y,S=x+y,T=this.top+f;else if(a==="left")x=g(this.right),j=this.right-f,N=x-y,E=g(t.left)+y,A=t.right;else if(a==="right")x=g(this.left),E=t.left,A=g(t.right)-y,j=x+y,N=this.left+f;else if(n==="x"){if(a==="center")x=g((t.top+t.bottom)/2+.5);else if($(a)){const U=Object.keys(a)[0],K=a[U];x=g(this.chart.scales[U].getPixelForValue(K))}L=t.top,q=t.bottom,S=x+y,T=S+f}else if(n==="y"){if(a==="center")x=g((t.left+t.right)/2);else if($(a)){const U=Object.keys(a)[0],K=a[U];x=g(this.chart.scales[U].getPixelForValue(K))}j=x-y,N=j-f,E=t.left,A=t.right}const ve=B(i.ticks.maxTicksLimit,h),W=Math.max(1,Math.ceil(h/ve));for(b=0;b<h;b+=W){const U=this.getContext(b),K=s.setContext(U),P=o.setContext(U),C=K.lineWidth,D=K.color,I=P.dash||[],J=P.dashOffset,yt=K.tickWidth,Re=K.tickColor,Ct=K.tickBorderDash||[],Le=K.tickBorderDashOffset;k=cw(this,b,l),k!==void 0&&(w=_n(r,k,C),u?j=N=E=A=w:S=T=L=q=w,p.push({tx1:j,ty1:S,tx2:N,ty2:T,x1:E,y1:L,x2:A,y2:q,width:C,color:D,borderDash:I,borderDashOffset:J,tickWidth:yt,tickColor:Re,tickBorderDash:Ct,tickBorderDashOffset:Le}))}return this._ticksLength=h,this._borderValue=x,p}_computeLabelItems(t){const n=this.axis,r=this.options,{position:i,ticks:s}=r,a=this.isHorizontal(),o=this.ticks,{align:l,crossAlign:u,padding:d,mirror:h}=s,f=ti(r.grid),p=f+d,m=h?-d:p,v=-Dn(this.labelRotation),y=[];let g,x,b,k,w,j,S,N,T,E,L,A,q="middle";if(i==="top")j=this.bottom-m,S=this._getXAxisLabelAlignment();else if(i==="bottom")j=this.top+m,S=this._getXAxisLabelAlignment();else if(i==="left"){const W=this._getYAxisLabelAlignment(f);S=W.textAlign,w=W.x}else if(i==="right"){const W=this._getYAxisLabelAlignment(f);S=W.textAlign,w=W.x}else if(n==="x"){if(i==="center")j=(t.top+t.bottom)/2+p;else if($(i)){const W=Object.keys(i)[0],U=i[W];j=this.chart.scales[W].getPixelForValue(U)+p}S=this._getXAxisLabelAlignment()}else if(n==="y"){if(i==="center")w=(t.left+t.right)/2-p;else if($(i)){const W=Object.keys(i)[0],U=i[W];w=this.chart.scales[W].getPixelForValue(U)}S=this._getYAxisLabelAlignment(f).textAlign}n==="y"&&(l==="start"?q="top":l==="end"&&(q="bottom"));const ve=this._getLabelSizes();for(g=0,x=o.length;g<x;++g){b=o[g],k=b.label;const W=s.setContext(this.getContext(g));N=this.getPixelForTick(g)+s.labelOffset,T=this._resolveTickFontOptions(g),E=T.lineHeight,L=pe(k)?k.length:1;const U=L/2,K=W.color,P=W.textStrokeColor,C=W.textStrokeWidth;let D=S;a?(w=N,S==="inner"&&(g===x-1?D=this.options.reverse?"left":"right":g===0?D=this.options.reverse?"right":"left":D="center"),i==="top"?u==="near"||v!==0?A=-L*E+E/2:u==="center"?A=-ve.highest.height/2-U*E+E:A=-ve.highest.height+E/2:u==="near"||v!==0?A=E/2:u==="center"?A=ve.highest.height/2-U*E:A=ve.highest.height-L*E,h&&(A*=-1),v!==0&&!W.showLabelBackdrop&&(w+=E/2*Math.sin(v))):(j=N,A=(1-L)*E/2);let I;if(W.showLabelBackdrop){const J=ct(W.backdropPadding),yt=ve.heights[g],Re=ve.widths[g];let Ct=A-J.top,Le=0-J.left;switch(q){case"middle":Ct-=yt/2;break;case"bottom":Ct-=yt;break}switch(S){case"center":Le-=Re/2;break;case"right":Le-=Re;break;case"inner":g===x-1?Le-=Re:g>0&&(Le-=Re/2);break}I={left:Le,top:Ct,width:Re+J.width,height:yt+J.height,color:W.backdropColor}}y.push({label:k,font:T,textOffset:A,options:{rotation:v,color:K,strokeColor:P,strokeWidth:C,textAlign:D,textBaseline:q,translation:[w,j],backdrop:I}})}return y}_getXAxisLabelAlignment(){const{position:t,ticks:n}=this.options;if(-Dn(this.labelRotation))return t==="top"?"left":"right";let i="center";return n.align==="start"?i="left":n.align==="end"?i="right":n.align==="inner"&&(i="inner"),i}_getYAxisLabelAlignment(t){const{position:n,ticks:{crossAlign:r,mirror:i,padding:s}}=this.options,a=this._getLabelSizes(),o=t+s,l=a.widest.width;let u,d;return n==="left"?i?(d=this.right+s,r==="near"?u="left":r==="center"?(u="center",d+=l/2):(u="right",d+=l)):(d=this.right-o,r==="near"?u="right":r==="center"?(u="center",d-=l/2):(u="left",d=this.left)):n==="right"?i?(d=this.left+s,r==="near"?u="right":r==="center"?(u="center",d-=l/2):(u="left",d-=l)):(d=this.left+o,r==="near"?u="left":r==="center"?(u="center",d+=l/2):(u="right",d=this.right)):u="right",{textAlign:u,x:d}}_computeLabelArea(){if(this.options.ticks.mirror)return;const t=this.chart,n=this.options.position;if(n==="left"||n==="right")return{top:0,left:this.left,bottom:t.height,right:this.right};if(n==="top"||n==="bottom")return{top:this.top,left:0,bottom:this.bottom,right:t.width}}drawBackground(){const{ctx:t,options:{backgroundColor:n},left:r,top:i,width:s,height:a}=this;n&&(t.save(),t.fillStyle=n,t.fillRect(r,i,s,a),t.restore())}getLineWidthForValue(t){const n=this.options.grid;if(!this._isVisible()||!n.display)return 0;const i=this.ticks.findIndex(s=>s.value===t);return i>=0?n.setContext(this.getContext(i)).lineWidth:0}drawGrid(t){const n=this.options.grid,r=this.ctx,i=this._gridLineItems||(this._gridLineItems=this._computeGridLineItems(t));let s,a;const o=(l,u,d)=>{!d.width||!d.color||(r.save(),r.lineWidth=d.width,r.strokeStyle=d.color,r.setLineDash(d.borderDash||[]),r.lineDashOffset=d.borderDashOffset,r.beginPath(),r.moveTo(l.x,l.y),r.lineTo(u.x,u.y),r.stroke(),r.restore())};if(n.display)for(s=0,a=i.length;s<a;++s){const l=i[s];n.drawOnChartArea&&o({x:l.x1,y:l.y1},{x:l.x2,y:l.y2},l),n.drawTicks&&o({x:l.tx1,y:l.ty1},{x:l.tx2,y:l.ty2},{color:l.tickColor,width:l.tickWidth,borderDash:l.tickBorderDash,borderDashOffset:l.tickBorderDashOffset})}}drawBorder(){const{chart:t,ctx:n,options:{border:r,grid:i}}=this,s=r.setContext(this.getContext()),a=r.display?s.width:0;if(!a)return;const o=i.setContext(this.getContext(0)).lineWidth,l=this._borderValue;let u,d,h,f;this.isHorizontal()?(u=_n(t,this.left,a)-a/2,d=_n(t,this.right,o)+o/2,h=f=l):(h=_n(t,this.top,a)-a/2,f=_n(t,this.bottom,o)+o/2,u=d=l),n.save(),n.lineWidth=s.width,n.strokeStyle=s.color,n.beginPath(),n.moveTo(u,h),n.lineTo(d,f),n.stroke(),n.restore()}drawLabels(t){if(!this.options.ticks.display)return;const r=this.ctx,i=this._computeLabelArea();i&&uo(r,i);const s=this.getLabelItems(t);for(const a of s){const o=a.options,l=a.font,u=a.label,d=a.textOffset;qi(r,u,0,d,l,o)}i&&ho(r)}drawTitle(){const{ctx:t,options:{position:n,title:r,reverse:i}}=this;if(!r.display)return;const s=Ee(r.font),a=ct(r.padding),o=r.align;let l=s.lineHeight/2;n==="bottom"||n==="center"||$(n)?(l+=a.bottom,pe(r.text)&&(l+=s.lineHeight*(r.text.length-1))):l+=a.top;const{titleX:u,titleY:d,maxWidth:h,rotation:f}=pw(this,l,n,o);qi(t,r.text,0,0,s,{color:r.color,maxWidth:h,rotation:f,textAlign:fw(o,n,i),textBaseline:"middle",translation:[u,d]})}draw(t){this._isVisible()&&(this.drawBackground(),this.drawGrid(t),this.drawBorder(),this.drawTitle(),this.drawLabels(t))}_layers(){const t=this.options,n=t.ticks&&t.ticks.z||0,r=B(t.grid&&t.grid.z,-1),i=B(t.border&&t.border.z,0);return!this._isVisible()||this.draw!==Hr.prototype.draw?[{z:n,draw:s=>{this.draw(s)}}]:[{z:r,draw:s=>{this.drawBackground(),this.drawGrid(s),this.drawTitle()}},{z:i,draw:()=>{this.drawBorder()}},{z:n,draw:s=>{this.drawLabels(s)}}]}getMatchingVisibleMetas(t){const n=this.chart.getSortedVisibleDatasetMetas(),r=this.axis+"AxisID",i=[];let s,a;for(s=0,a=n.length;s<a;++s){const o=n[s];o[r]===this.id&&(!t||o.type===t)&&i.push(o)}return i}_resolveTickFontOptions(t){const n=this.options.ticks.setContext(this.getContext(t));return Ee(n.font)}_maxDigits(){const t=this._resolveTickFontOptions(0).lineHeight;return(this.isHorizontal()?this.width:this.height)/t}}class Bs{constructor(t,n,r){this.type=t,this.scope=n,this.override=r,this.items=Object.create(null)}isForType(t){return Object.prototype.isPrototypeOf.call(this.type.prototype,t.prototype)}register(t){const n=Object.getPrototypeOf(t);let r;vw(n)&&(r=this.register(n));const i=this.items,s=t.id,a=this.scope+"."+s;if(!s)throw new Error("class does not have id: "+t);return s in i||(i[s]=t,mw(t,a,r),this.override&&ue.override(t.id,t.overrides)),a}get(t){return this.items[t]}unregister(t){const n=this.items,r=t.id,i=this.scope;r in n&&delete n[r],i&&r in ue[i]&&(delete ue[i][r],this.override&&delete Kn[r])}}function mw(e,t,n){const r=Qi(Object.create(null),[n?ue.get(n):{},ue.get(t),e.defaults]);ue.set(t,r),e.defaultRoutes&&gw(t,e.defaultRoutes),e.descriptors&&ue.describe(t,e.descriptors)}function gw(e,t){Object.keys(t).forEach(n=>{const r=n.split("."),i=r.pop(),s=[e].concat(r).join("."),a=t[n].split("."),o=a.pop(),l=a.join(".");ue.route(s,i,l,o)})}function vw(e){return"id"in e&&"defaults"in e}class yw{constructor(){this.controllers=new Bs(Si,"datasets",!0),this.elements=new Bs(vt,"elements"),this.plugins=new Bs(Object,"plugins"),this.scales=new Bs(Hr,"scales"),this._typedRegistries=[this.controllers,this.scales,this.elements]}add(...t){this._each("register",t)}remove(...t){this._each("unregister",t)}addControllers(...t){this._each("register",t,this.controllers)}addElements(...t){this._each("register",t,this.elements)}addPlugins(...t){this._each("register",t,this.plugins)}addScales(...t){this._each("register",t,this.scales)}getController(t){return this._get(t,this.controllers,"controller")}getElement(t){return this._get(t,this.elements,"element")}getPlugin(t){return this._get(t,this.plugins,"plugin")}getScale(t){return this._get(t,this.scales,"scale")}removeControllers(...t){this._each("unregister",t,this.controllers)}removeElements(...t){this._each("unregister",t,this.elements)}removePlugins(...t){this._each("unregister",t,this.plugins)}removeScales(...t){this._each("unregister",t,this.scales)}_each(t,n,r){[...n].forEach(i=>{const s=r||this._getRegistryForType(i);r||s.isForType(i)||s===this.plugins&&i.id?this._exec(t,s,i):Y(i,a=>{const o=r||this._getRegistryForType(a);this._exec(t,o,a)})})}_exec(t,n,r){const i=bu(t);te(r["before"+i],[],r),n[t](r),te(r["after"+i],[],r)}_getRegistryForType(t){for(let n=0;n<this._typedRegistries.length;n++){const r=this._typedRegistries[n];if(r.isForType(t))return r}return this.plugins}_get(t,n,r){const i=n.get(t);if(i===void 0)throw new Error('"'+t+'" is not a registered '+r+".");return i}}var _t=new yw;class xw{constructor(){this._init=void 0}notify(t,n,r,i){if(n==="beforeInit"&&(this._init=this._createDescriptors(t,!0),this._notify(this._init,t,"install")),this._init===void 0)return;const s=i?this._descriptors(t).filter(i):this._descriptors(t),a=this._notify(s,t,n,r);return n==="afterDestroy"&&(this._notify(s,t,"stop"),this._notify(this._init,t,"uninstall"),this._init=void 0),a}_notify(t,n,r,i){i=i||{};for(const s of t){const a=s.plugin,o=a[r],l=[n,i,s.options];if(te(o,l,a)===!1&&i.cancelable)return!1}return!0}invalidate(){Z(this._cache)||(this._oldCache=this._cache,this._cache=void 0)}_descriptors(t){if(this._cache)return this._cache;const n=this._cache=this._createDescriptors(t);return this._notifyStateChanges(t),n}_createDescriptors(t,n){const r=t&&t.config,i=B(r.options&&r.options.plugins,{}),s=bw(r);return i===!1&&!n?[]:ww(t,s,i,n)}_notifyStateChanges(t){const n=this._oldCache||[],r=this._cache,i=(s,a)=>s.filter(o=>!a.some(l=>o.plugin.id===l.plugin.id));this._notify(i(n,r),t,"stop"),this._notify(i(r,n),t,"start")}}function bw(e){const t={},n=[],r=Object.keys(_t.plugins.items);for(let s=0;s<r.length;s++)n.push(_t.getPlugin(r[s]));const i=e.plugins||[];for(let s=0;s<i.length;s++){const a=i[s];n.indexOf(a)===-1&&(n.push(a),t[a.id]=!0)}return{plugins:n,localIds:t}}function kw(e,t){return!t&&e===!1?null:e===!0?{}:e}function ww(e,{plugins:t,localIds:n},r,i){const s=[],a=e.getContext();for(const o of t){const l=o.id,u=kw(r[l],i);u!==null&&s.push({plugin:o,options:_w(e.config,{plugin:o,local:n[l]},u,a)})}return s}function _w(e,{plugin:t,local:n},r,i){const s=e.pluginScopeKeys(t),a=e.getOptionScopes(r,s);return n&&t.defaults&&a.push(t.defaults),e.createResolver(a,i,[""],{scriptable:!1,indexable:!1,allKeys:!0})}function cc(e,t){const n=ue.datasets[e]||{};return((t.datasets||{})[e]||{}).indexAxis||t.indexAxis||n.indexAxis||"x"}function jw(e,t){let n=e;return e==="_index_"?n=t:e==="_value_"&&(n=t==="x"?"y":"x"),n}function Sw(e,t){return e===t?"_index_":"_value_"}function Fh(e){if(e==="x"||e==="y"||e==="r")return e}function Nw(e){if(e==="top"||e==="bottom")return"x";if(e==="left"||e==="right")return"y"}function uc(e,...t){if(Fh(e))return e;for(const n of t){const r=n.axis||Nw(n.position)||e.length>1&&Fh(e[0].toLowerCase());if(r)return r}throw new Error(`Cannot determine type of '${e}' axis. Please provide 'axis' or 'position' option.`)}function Bh(e,t,n){if(n[t+"AxisID"]===e)return{axis:t}}function Cw(e,t){if(t.data&&t.data.datasets){const n=t.data.datasets.filter(r=>r.xAxisID===e||r.yAxisID===e);if(n.length)return Bh(e,"x",n[0])||Bh(e,"y",n[0])}return{}}function Mw(e,t){const n=Kn[e.type]||{scales:{}},r=t.scales||{},i=cc(e.type,t),s=Object.create(null);return Object.keys(r).forEach(a=>{const o=r[a];if(!$(o))return console.error(`Invalid scale configuration for scale: ${a}`);if(o._proxy)return console.warn(`Ignoring resolver passed as options for scale: ${a}`);const l=uc(a,o,Cw(a,e),ue.scales[o.type]),u=Sw(l,i),d=n.scales||{};s[a]=ki(Object.create(null),[{axis:l},o,d[l],d[u]])}),e.data.datasets.forEach(a=>{const o=a.type||e.type,l=a.indexAxis||cc(o,t),d=(Kn[o]||{}).scales||{};Object.keys(d).forEach(h=>{const f=jw(h,l),p=a[f+"AxisID"]||f;s[p]=s[p]||Object.create(null),ki(s[p],[{axis:f},r[p],d[h]])})}),Object.keys(s).forEach(a=>{const o=s[a];ki(o,[ue.scales[o.type],ue.scale])}),s}function Bg(e){const t=e.options||(e.options={});t.plugins=B(t.plugins,{}),t.scales=Mw(e,t)}function $g(e){return e=e||{},e.datasets=e.datasets||[],e.labels=e.labels||[],e}function Pw(e){return e=e||{},e.data=$g(e.data),Bg(e),e}const $h=new Map,Hg=new Set;function $s(e,t){let n=$h.get(e);return n||(n=t(),$h.set(e,n),Hg.add(n)),n}const ni=(e,t,n)=>{const r=Oa(t,n);r!==void 0&&e.add(r)};class Ew{constructor(t){this._config=Pw(t),this._scopeCache=new Map,this._resolverCache=new Map}get platform(){return this._config.platform}get type(){return this._config.type}set type(t){this._config.type=t}get data(){return this._config.data}set data(t){this._config.data=$g(t)}get options(){return this._config.options}set options(t){this._config.options=t}get plugins(){return this._config.plugins}update(){const t=this._config;this.clearCache(),Bg(t)}clearCache(){this._scopeCache.clear(),this._resolverCache.clear()}datasetScopeKeys(t){return $s(t,()=>[[`datasets.${t}`,""]])}datasetAnimationScopeKeys(t,n){return $s(`${t}.transition.${n}`,()=>[[`datasets.${t}.transitions.${n}`,`transitions.${n}`],[`datasets.${t}`,""]])}datasetElementScopeKeys(t,n){return $s(`${t}-${n}`,()=>[[`datasets.${t}.elements.${n}`,`datasets.${t}`,`elements.${n}`,""]])}pluginScopeKeys(t){const n=t.id,r=this.type;return $s(`${r}-plugin-${n}`,()=>[[`plugins.${n}`,...t.additionalOptionScopes||[]]])}_cachedScopes(t,n){const r=this._scopeCache;let i=r.get(t);return(!i||n)&&(i=new Map,r.set(t,i)),i}getOptionScopes(t,n,r){const{options:i,type:s}=this,a=this._cachedScopes(t,r),o=a.get(n);if(o)return o;const l=new Set;n.forEach(d=>{t&&(l.add(t),d.forEach(h=>ni(l,t,h))),d.forEach(h=>ni(l,i,h)),d.forEach(h=>ni(l,Kn[s]||{},h)),d.forEach(h=>ni(l,ue,h)),d.forEach(h=>ni(l,oc,h))});const u=Array.from(l);return u.length===0&&u.push(Object.create(null)),Hg.has(n)&&a.set(n,u),u}chartOptionScopes(){const{options:t,type:n}=this;return[t,Kn[n]||{},ue.datasets[n]||{},{type:n},ue,oc]}resolveNamedOptions(t,n,r,i=[""]){const s={$shared:!0},{resolver:a,subPrefixes:o}=Hh(this._resolverCache,t,i);let l=a;if(zw(a,n)){s.$shared=!1,r=vn(r)?r():r;const u=this.createResolver(t,r,o);l=Dr(a,r,u)}for(const u of n)s[u]=l[u];return s}createResolver(t,n,r=[""],i){const{resolver:s}=Hh(this._resolverCache,t,r);return $(n)?Dr(s,n,void 0,i):s}}function Hh(e,t,n){let r=e.get(t);r||(r=new Map,e.set(t,r));const i=n.join();let s=r.get(i);return s||(s={resolver:Nu(t,n),subPrefixes:n.filter(o=>!o.toLowerCase().includes("hover"))},r.set(i,s)),s}const Tw=e=>$(e)&&Object.getOwnPropertyNames(e).some(t=>vn(e[t]));function zw(e,t){const{isScriptable:n,isIndexable:r}=wg(e);for(const i of t){const s=n(i),a=r(i),o=(a||s)&&e[i];if(s&&(vn(o)||Tw(o))||a&&pe(o))return!0}return!1}var Dw="4.5.1";const Rw=["top","bottom","left","right","chartArea"];function Wh(e,t){return e==="top"||e==="bottom"||Rw.indexOf(e)===-1&&t==="x"}function Vh(e,t){return function(n,r){return n[e]===r[e]?n[t]-r[t]:n[e]-r[e]}}function Uh(e){const t=e.chart,n=t.options.animation;t.notifyPlugins("afterRender"),te(n&&n.onComplete,[e],t)}function Lw(e){const t=e.chart,n=t.options.animation;te(n&&n.onProgress,[e],t)}function Wg(e){return Pu()&&typeof e=="string"?e=document.getElementById(e):e&&e.length&&(e=e[0]),e&&e.canvas&&(e=e.canvas),e}const sa={},Yh=e=>{const t=Wg(e);return Object.values(sa).filter(n=>n.canvas===t).pop()};function Ow(e,t,n){const r=Object.keys(e);for(const i of r){const s=+i;if(s>=t){const a=e[i];delete e[i],(n>0||s>t)&&(e[s+n]=a)}}}function Aw(e,t,n,r){return!n||e.type==="mouseout"?null:r?t:e}var Ut;let Wr=(Ut=class{static register(...t){_t.add(...t),Xh()}static unregister(...t){_t.remove(...t),Xh()}constructor(t,n){const r=this.config=new Ew(n),i=Wg(t),s=Yh(i);if(s)throw new Error("Canvas is already in use. Chart with ID '"+s.id+"' must be destroyed before the canvas with ID '"+s.canvas.id+"' can be reused.");const a=r.createResolver(r.chartOptionScopes(),this.getContext());this.platform=new(r.platform||tw(i)),this.platform.updateConfig(r);const o=this.platform.acquireContext(i,a.aspectRatio),l=o&&o.canvas,u=l&&l.height,d=l&&l.width;if(this.id=U1(),this.ctx=o,this.canvas=l,this.width=d,this.height=u,this._options=a,this._aspectRatio=this.aspectRatio,this._layers=[],this._metasets=[],this._stacks=void 0,this.boxes=[],this.currentDevicePixelRatio=void 0,this.chartArea=void 0,this._active=[],this._lastEvent=void 0,this._listeners={},this._responsiveListeners=void 0,this._sortedMetasets=[],this.scales={},this._plugins=new xw,this.$proxies={},this._hiddenIndices={},this.attached=!1,this._animationsDisabled=void 0,this.$context=void 0,this._doResize=db(h=>this.update(h),a.resizeDelay||0),this._dataChanges=[],sa[this.id]=this,!o||!l){console.error("Failed to create chart: can't acquire context from the given item");return}Et.listen(this,"complete",Uh),Et.listen(this,"progress",Lw),this._initialize(),this.attached&&this.update()}get aspectRatio(){const{options:{aspectRatio:t,maintainAspectRatio:n},width:r,height:i,_aspectRatio:s}=this;return Z(t)?n&&s?s:i?r/i:null:t}get data(){return this.config.data}set data(t){this.config.data=t}get options(){return this._options}set options(t){this.config.options=t}get registry(){return _t}_initialize(){return this.notifyPlugins("beforeInit"),this.options.responsive?this.resize():yh(this,this.options.devicePixelRatio),this.bindEvents(),this.notifyPlugins("afterInit"),this}clear(){return mh(this.canvas,this.ctx),this}stop(){return Et.stop(this),this}resize(t,n){Et.running(this)?this._resizeBeforeDraw={width:t,height:n}:this._resize(t,n)}_resize(t,n){const r=this.options,i=this.canvas,s=r.maintainAspectRatio&&this.aspectRatio,a=this.platform.getMaximumSize(i,t,n,s),o=r.devicePixelRatio||this.platform.getDevicePixelRatio(),l=this.width?"resize":"attach";this.width=a.width,this.height=a.height,this._aspectRatio=this.aspectRatio,yh(this,o,!0)&&(this.notifyPlugins("resize",{size:a}),te(r.onResize,[this,a],this),this.attached&&this._doResize(l)&&this.render())}ensureScalesHaveIDs(){const n=this.options.scales||{};Y(n,(r,i)=>{r.id=i})}buildOrUpdateScales(){const t=this.options,n=t.scales,r=this.scales,i=Object.keys(r).reduce((a,o)=>(a[o]=!1,a),{});let s=[];n&&(s=s.concat(Object.keys(n).map(a=>{const o=n[a],l=uc(a,o),u=l==="r",d=l==="x";return{options:o,dposition:u?"chartArea":d?"bottom":"left",dtype:u?"radialLinear":d?"category":"linear"}}))),Y(s,a=>{const o=a.options,l=o.id,u=uc(l,o),d=B(o.type,a.dtype);(o.position===void 0||Wh(o.position,u)!==Wh(a.dposition))&&(o.position=a.dposition),i[l]=!0;let h=null;if(l in r&&r[l].type===d)h=r[l];else{const f=_t.getScale(d);h=new f({id:l,type:d,ctx:this.ctx,chart:this}),r[h.id]=h}h.init(o,t)}),Y(i,(a,o)=>{a||delete r[o]}),Y(r,a=>{st.configure(this,a,a.options),st.addBox(this,a)})}_updateMetasets(){const t=this._metasets,n=this.data.datasets.length,r=t.length;if(t.sort((i,s)=>i.index-s.index),r>n){for(let i=n;i<r;++i)this._destroyDatasetMeta(i);t.splice(n,r-n)}this._sortedMetasets=t.slice(0).sort(Vh("order","index"))}_removeUnreferencedMetasets(){const{_metasets:t,data:{datasets:n}}=this;t.length>n.length&&delete this._stacks,t.forEach((r,i)=>{n.filter(s=>s===r._dataset).length===0&&this._destroyDatasetMeta(i)})}buildOrUpdateControllers(){const t=[],n=this.data.datasets;let r,i;for(this._removeUnreferencedMetasets(),r=0,i=n.length;r<i;r++){const s=n[r];let a=this.getDatasetMeta(r);const o=s.type||this.config.type;if(a.type&&a.type!==o&&(this._destroyDatasetMeta(r),a=this.getDatasetMeta(r)),a.type=o,a.indexAxis=s.indexAxis||cc(o,this.options),a.order=s.order||0,a.index=r,a.label=""+s.label,a.visible=this.isDatasetVisible(r),a.controller)a.controller.updateIndex(r),a.controller.linkScales();else{const l=_t.getController(o),{datasetElementType:u,dataElementType:d}=ue.datasets[o];Object.assign(l,{dataElementType:_t.getElement(d),datasetElementType:u&&_t.getElement(u)}),a.controller=new l(this,r),t.push(a.controller)}}return this._updateMetasets(),t}_resetElements(){Y(this.data.datasets,(t,n)=>{this.getDatasetMeta(n).controller.reset()},this)}reset(){this._resetElements(),this.notifyPlugins("reset")}update(t){const n=this.config;n.update();const r=this._options=n.createResolver(n.chartOptionScopes(),this.getContext()),i=this._animationsDisabled=!r.animation;if(this._updateScales(),this._checkEventBindings(),this._updateHiddenIndices(),this._plugins.invalidate(),this.notifyPlugins("beforeUpdate",{mode:t,cancelable:!0})===!1)return;const s=this.buildOrUpdateControllers();this.notifyPlugins("beforeElementsUpdate");let a=0;for(let u=0,d=this.data.datasets.length;u<d;u++){const{controller:h}=this.getDatasetMeta(u),f=!i&&s.indexOf(h)===-1;h.buildOrUpdateElements(f),a=Math.max(+h.getMaxOverflow(),a)}a=this._minPadding=r.layout.autoPadding?a:0,this._updateLayout(a),i||Y(s,u=>{u.reset()}),this._updateDatasets(t),this.notifyPlugins("afterUpdate",{mode:t}),this._layers.sort(Vh("z","_idx"));const{_active:o,_lastEvent:l}=this;l?this._eventHandler(l,!0):o.length&&this._updateHoverStyles(o,o,!0),this.render()}_updateScales(){Y(this.scales,t=>{st.removeBox(this,t)}),this.ensureScalesHaveIDs(),this.buildOrUpdateScales()}_checkEventBindings(){const t=this.options,n=new Set(Object.keys(this._listeners)),r=new Set(t.events);(!sh(n,r)||!!this._responsiveListeners!==t.responsive)&&(this.unbindEvents(),this.bindEvents())}_updateHiddenIndices(){const{_hiddenIndices:t}=this,n=this._getUniformDataChanges()||[];for(const{method:r,start:i,count:s}of n){const a=r==="_removeElements"?-s:s;Ow(t,i,a)}}_getUniformDataChanges(){const t=this._dataChanges;if(!t||!t.length)return;this._dataChanges=[];const n=this.data.datasets.length,r=s=>new Set(t.filter(a=>a[0]===s).map((a,o)=>o+","+a.splice(1).join(","))),i=r(0);for(let s=1;s<n;s++)if(!sh(i,r(s)))return;return Array.from(i).map(s=>s.split(",")).map(s=>({method:s[1],start:+s[2],count:+s[3]}))}_updateLayout(t){if(this.notifyPlugins("beforeLayout",{cancelable:!0})===!1)return;st.update(this,this.width,this.height,t);const n=this.chartArea,r=n.width<=0||n.height<=0;this._layers=[],Y(this.boxes,i=>{r&&i.position==="chartArea"||(i.configure&&i.configure(),this._layers.push(...i._layers()))},this),this._layers.forEach((i,s)=>{i._idx=s}),this.notifyPlugins("afterLayout")}_updateDatasets(t){if(this.notifyPlugins("beforeDatasetsUpdate",{mode:t,cancelable:!0})!==!1){for(let n=0,r=this.data.datasets.length;n<r;++n)this.getDatasetMeta(n).controller.configure();for(let n=0,r=this.data.datasets.length;n<r;++n)this._updateDataset(n,vn(t)?t({datasetIndex:n}):t);this.notifyPlugins("afterDatasetsUpdate",{mode:t})}}_updateDataset(t,n){const r=this.getDatasetMeta(t),i={meta:r,index:t,mode:n,cancelable:!0};this.notifyPlugins("beforeDatasetUpdate",i)!==!1&&(r.controller._update(n),i.cancelable=!1,this.notifyPlugins("afterDatasetUpdate",i))}render(){this.notifyPlugins("beforeRender",{cancelable:!0})!==!1&&(Et.has(this)?this.attached&&!Et.running(this)&&Et.start(this):(this.draw(),Uh({chart:this})))}draw(){let t;if(this._resizeBeforeDraw){const{width:r,height:i}=this._resizeBeforeDraw;this._resizeBeforeDraw=null,this._resize(r,i)}if(this.clear(),this.width<=0||this.height<=0||this.notifyPlugins("beforeDraw",{cancelable:!0})===!1)return;const n=this._layers;for(t=0;t<n.length&&n[t].z<=0;++t)n[t].draw(this.chartArea);for(this._drawDatasets();t<n.length;++t)n[t].draw(this.chartArea);this.notifyPlugins("afterDraw")}_getSortedDatasetMetas(t){const n=this._sortedMetasets,r=[];let i,s;for(i=0,s=n.length;i<s;++i){const a=n[i];(!t||a.visible)&&r.push(a)}return r}getSortedVisibleDatasetMetas(){return this._getSortedDatasetMetas(!0)}_drawDatasets(){if(this.notifyPlugins("beforeDatasetsDraw",{cancelable:!0})===!1)return;const t=this.getSortedVisibleDatasetMetas();for(let n=t.length-1;n>=0;--n)this._drawDataset(t[n]);this.notifyPlugins("afterDatasetsDraw")}_drawDataset(t){const n=this.ctx,r={meta:t,index:t.index,cancelable:!0},i=zg(this,t);this.notifyPlugins("beforeDatasetDraw",r)!==!1&&(i&&uo(n,i),t.controller.draw(),i&&ho(n),r.cancelable=!1,this.notifyPlugins("afterDatasetDraw",r))}isPointInArea(t){return Zi(t,this.chartArea,this._minPadding)}getElementsAtEventForMode(t,n,r,i){const s=Rk.modes[n];return typeof s=="function"?s(this,t,r,i):[]}getDatasetMeta(t){const n=this.data.datasets[t],r=this._metasets;let i=r.filter(s=>s&&s._dataset===n).pop();return i||(i={type:null,data:[],dataset:null,controller:null,hidden:null,xAxisID:null,yAxisID:null,order:n&&n.order||0,index:t,_dataset:n,_parsed:[],_sorted:!1},r.push(i)),i}getContext(){return this.$context||(this.$context=qn(null,{chart:this,type:"chart"}))}getVisibleDatasetCount(){return this.getSortedVisibleDatasetMetas().length}isDatasetVisible(t){const n=this.data.datasets[t];if(!n)return!1;const r=this.getDatasetMeta(t);return typeof r.hidden=="boolean"?!r.hidden:!n.hidden}setDatasetVisibility(t,n){const r=this.getDatasetMeta(t);r.hidden=!n}toggleDataVisibility(t){this._hiddenIndices[t]=!this._hiddenIndices[t]}getDataVisibility(t){return!this._hiddenIndices[t]}_updateVisibility(t,n,r){const i=r?"show":"hide",s=this.getDatasetMeta(t),a=s.controller._resolveAnimations(void 0,i);Aa(n)?(s.data[n].hidden=!r,this.update()):(this.setDatasetVisibility(t,r),a.update(s,{visible:r}),this.update(o=>o.datasetIndex===t?i:void 0))}hide(t,n){this._updateVisibility(t,n,!1)}show(t,n){this._updateVisibility(t,n,!0)}_destroyDatasetMeta(t){const n=this._metasets[t];n&&n.controller&&n.controller._destroy(),delete this._metasets[t]}_stop(){let t,n;for(this.stop(),Et.remove(this),t=0,n=this.data.datasets.length;t<n;++t)this._destroyDatasetMeta(t)}destroy(){this.notifyPlugins("beforeDestroy");const{canvas:t,ctx:n}=this;this._stop(),this.config.clearCache(),t&&(this.unbindEvents(),mh(t,n),this.platform.releaseContext(n),this.canvas=null,this.ctx=null),delete sa[this.id],this.notifyPlugins("afterDestroy")}toBase64Image(...t){return this.canvas.toDataURL(...t)}bindEvents(){this.bindUserEvents(),this.options.responsive?this.bindResponsiveEvents():this.attached=!0}bindUserEvents(){const t=this._listeners,n=this.platform,r=(s,a)=>{n.addEventListener(this,s,a),t[s]=a},i=(s,a,o)=>{s.offsetX=a,s.offsetY=o,this._eventHandler(s)};Y(this.options.events,s=>r(s,i))}bindResponsiveEvents(){this._responsiveListeners||(this._responsiveListeners={});const t=this._responsiveListeners,n=this.platform,r=(l,u)=>{n.addEventListener(this,l,u),t[l]=u},i=(l,u)=>{t[l]&&(n.removeEventListener(this,l,u),delete t[l])},s=(l,u)=>{this.canvas&&this.resize(l,u)};let a;const o=()=>{i("attach",o),this.attached=!0,this.resize(),r("resize",s),r("detach",a)};a=()=>{this.attached=!1,i("resize",s),this._stop(),this._resize(0,0),r("attach",o)},n.isAttached(this.canvas)?o():a()}unbindEvents(){Y(this._listeners,(t,n)=>{this.platform.removeEventListener(this,n,t)}),this._listeners={},Y(this._responsiveListeners,(t,n)=>{this.platform.removeEventListener(this,n,t)}),this._responsiveListeners=void 0}updateHoverStyle(t,n,r){const i=r?"set":"remove";let s,a,o,l;for(n==="dataset"&&(s=this.getDatasetMeta(t[0].datasetIndex),s.controller["_"+i+"DatasetHoverStyle"]()),o=0,l=t.length;o<l;++o){a=t[o];const u=a&&this.getDatasetMeta(a.datasetIndex).controller;u&&u[i+"HoverStyle"](a.element,a.datasetIndex,a.index)}}getActiveElements(){return this._active||[]}setActiveElements(t){const n=this._active||[],r=t.map(({datasetIndex:s,index:a})=>{const o=this.getDatasetMeta(s);if(!o)throw new Error("No dataset found at index "+s);return{datasetIndex:s,element:o.data[a],index:a}});!Ra(r,n)&&(this._active=r,this._lastEvent=null,this._updateHoverStyles(r,n))}notifyPlugins(t,n,r){return this._plugins.notify(this,t,n,r)}isPluginEnabled(t){return this._plugins._cache.filter(n=>n.plugin.id===t).length===1}_updateHoverStyles(t,n,r){const i=this.options.hover,s=(l,u)=>l.filter(d=>!u.some(h=>d.datasetIndex===h.datasetIndex&&d.index===h.index)),a=s(n,t),o=r?t:s(t,n);a.length&&this.updateHoverStyle(a,i.mode,!1),o.length&&i.mode&&this.updateHoverStyle(o,i.mode,!0)}_eventHandler(t,n){const r={event:t,replay:n,cancelable:!0,inChartArea:this.isPointInArea(t)},i=a=>(a.options.events||this.options.events).includes(t.native.type);if(this.notifyPlugins("beforeEvent",r,i)===!1)return;const s=this._handleEvent(t,n,r.inChartArea);return r.cancelable=!1,this.notifyPlugins("afterEvent",r,i),(s||r.changed)&&this.render(),this}_handleEvent(t,n,r){const{_active:i=[],options:s}=this,a=n,o=this._getActiveElements(t,i,r,a),l=Z1(t),u=Aw(t,this._lastEvent,r,l);r&&(this._lastEvent=null,te(s.onHover,[t,o,this],this),l&&te(s.onClick,[t,o,this],this));const d=!Ra(o,i);return(d||n)&&(this._active=o,this._updateHoverStyles(o,i,n)),this._lastEvent=u,d}_getActiveElements(t,n,r,i){if(t.type==="mouseout")return[];if(!r)return n;const s=this.options.hover;return this.getElementsAtEventForMode(t,s.mode,s,i)}},R(Ut,"defaults",ue),R(Ut,"instances",sa),R(Ut,"overrides",Kn),R(Ut,"registry",_t),R(Ut,"version",Dw),R(Ut,"getChart",Yh),Ut);function Xh(){return Y(Wr.instances,e=>e._plugins.invalidate())}function Iw(e,t,n){const{startAngle:r,x:i,y:s,outerRadius:a,innerRadius:o,options:l}=t,{borderWidth:u,borderJoinStyle:d}=l,h=Math.min(u/a,Qe(r-n));if(e.beginPath(),e.arc(i,s,a-u/2,r+h/2,n-h/2),o>0){const f=Math.min(u/o,Qe(r-n));e.arc(i,s,o+u/2,n-f/2,r+f/2,!0)}else{const f=Math.min(u/2,a*Qe(r-n));if(d==="round")e.arc(i,s,f,n-Q/2,r+Q/2,!0);else if(d==="bevel"){const p=2*f*f,m=-p*Math.cos(n+Q/2)+i,v=-p*Math.sin(n+Q/2)+s,y=p*Math.cos(r+Q/2)+i,g=p*Math.sin(r+Q/2)+s;e.lineTo(m,v),e.lineTo(y,g)}}e.closePath(),e.moveTo(0,0),e.rect(0,0,e.canvas.width,e.canvas.height),e.clip("evenodd")}function Fw(e,t,n){const{startAngle:r,pixelMargin:i,x:s,y:a,outerRadius:o,innerRadius:l}=t;let u=i/o;e.beginPath(),e.arc(s,a,o,r-u,n+u),l>i?(u=i/l,e.arc(s,a,l,n+u,r-u,!0)):e.arc(s,a,i,n+we,r-we),e.closePath(),e.clip()}function Bw(e){return Su(e,["outerStart","outerEnd","innerStart","innerEnd"])}function $w(e,t,n,r){const i=Bw(e.options.borderRadius),s=(n-t)/2,a=Math.min(s,r*t/2),o=l=>{const u=(n-Math.min(s,l))*r/2;return Pe(l,0,Math.min(s,u))};return{outerStart:o(i.outerStart),outerEnd:o(i.outerEnd),innerStart:Pe(i.innerStart,0,a),innerEnd:Pe(i.innerEnd,0,a)}}function tr(e,t,n,r){return{x:n+e*Math.cos(t),y:r+e*Math.sin(t)}}function Ha(e,t,n,r,i,s){const{x:a,y:o,startAngle:l,pixelMargin:u,innerRadius:d}=t,h=Math.max(t.outerRadius+r+n-u,0),f=d>0?d+r+n+u:0;let p=0;const m=i-l;if(r){const W=d>0?d-r:0,U=h>0?h-r:0,K=(W+U)/2,P=K!==0?m*K/(K+r):m;p=(m-P)/2}const v=Math.max(.001,m*h-n/Q)/h,y=(m-v)/2,g=l+y+p,x=i-y-p,{outerStart:b,outerEnd:k,innerStart:w,innerEnd:j}=$w(t,f,h,x-g),S=h-b,N=h-k,T=g+b/S,E=x-k/N,L=f+w,A=f+j,q=g+w/L,ve=x-j/A;if(e.beginPath(),s){const W=(T+E)/2;if(e.arc(a,o,h,T,W),e.arc(a,o,h,W,E),k>0){const C=tr(N,E,a,o);e.arc(C.x,C.y,k,E,x+we)}const U=tr(A,x,a,o);if(e.lineTo(U.x,U.y),j>0){const C=tr(A,ve,a,o);e.arc(C.x,C.y,j,x+we,ve+Math.PI)}const K=(x-j/f+(g+w/f))/2;if(e.arc(a,o,f,x-j/f,K,!0),e.arc(a,o,f,K,g+w/f,!0),w>0){const C=tr(L,q,a,o);e.arc(C.x,C.y,w,q+Math.PI,g-we)}const P=tr(S,g,a,o);if(e.lineTo(P.x,P.y),b>0){const C=tr(S,T,a,o);e.arc(C.x,C.y,b,g-we,T)}}else{e.moveTo(a,o);const W=Math.cos(T)*h+a,U=Math.sin(T)*h+o;e.lineTo(W,U);const K=Math.cos(E)*h+a,P=Math.sin(E)*h+o;e.lineTo(K,P)}e.closePath()}function Hw(e,t,n,r,i){const{fullCircles:s,startAngle:a,circumference:o}=t;let l=t.endAngle;if(s){Ha(e,t,n,r,l,i);for(let u=0;u<s;++u)e.fill();isNaN(o)||(l=a+(o%be||be))}return Ha(e,t,n,r,l,i),e.fill(),l}function Ww(e,t,n,r,i){const{fullCircles:s,startAngle:a,circumference:o,options:l}=t,{borderWidth:u,borderJoinStyle:d,borderDash:h,borderDashOffset:f,borderRadius:p}=l,m=l.borderAlign==="inner";if(!u)return;e.setLineDash(h||[]),e.lineDashOffset=f,m?(e.lineWidth=u*2,e.lineJoin=d||"round"):(e.lineWidth=u,e.lineJoin=d||"bevel");let v=t.endAngle;if(s){Ha(e,t,n,r,v,i);for(let y=0;y<s;++y)e.stroke();isNaN(o)||(v=a+(o%be||be))}m&&Fw(e,t,v),l.selfJoin&&v-a>=Q&&p===0&&d!=="miter"&&Iw(e,t,v),s||(Ha(e,t,n,r,v,i),e.stroke())}class ui extends vt{constructor(n){super();R(this,"circumference");R(this,"endAngle");R(this,"fullCircles");R(this,"innerRadius");R(this,"outerRadius");R(this,"pixelMargin");R(this,"startAngle");this.options=void 0,this.circumference=void 0,this.startAngle=void 0,this.endAngle=void 0,this.innerRadius=void 0,this.outerRadius=void 0,this.pixelMargin=0,this.fullCircles=0,n&&Object.assign(this,n)}inRange(n,r,i){const s=this.getProps(["x","y"],i),{angle:a,distance:o}=pg(s,{x:n,y:r}),{startAngle:l,endAngle:u,innerRadius:d,outerRadius:h,circumference:f}=this.getProps(["startAngle","endAngle","innerRadius","outerRadius","circumference"],i),p=(this.options.spacing+this.options.borderWidth)/2,m=B(f,u-l),v=ku(a,l,u)&&l!==u,y=m>=be||v,g=At(o,d+p,h+p);return y&&g}getCenterPoint(n){const{x:r,y:i,startAngle:s,endAngle:a,innerRadius:o,outerRadius:l}=this.getProps(["x","y","startAngle","endAngle","innerRadius","outerRadius"],n),{offset:u,spacing:d}=this.options,h=(s+a)/2,f=(o+l+d+u)/2;return{x:r+Math.cos(h)*f,y:i+Math.sin(h)*f}}tooltipPosition(n){return this.getCenterPoint(n)}draw(n){const{options:r,circumference:i}=this,s=(r.offset||0)/4,a=(r.spacing||0)/2,o=r.circular;if(this.pixelMargin=r.borderAlign==="inner"?.33:0,this.fullCircles=i>be?Math.floor(i/be):0,i===0||this.innerRadius<0||this.outerRadius<0)return;n.save();const l=(this.startAngle+this.endAngle)/2;n.translate(Math.cos(l)*s,Math.sin(l)*s);const u=1-Math.sin(Math.min(Q,i||0)),d=s*u;n.fillStyle=r.backgroundColor,n.strokeStyle=r.borderColor,Hw(n,this,d,a,o),Ww(n,this,d,a,o),n.restore()}}R(ui,"id","arc"),R(ui,"defaults",{borderAlign:"center",borderColor:"#fff",borderDash:[],borderDashOffset:0,borderJoinStyle:void 0,borderRadius:0,borderWidth:2,offset:0,spacing:0,angle:void 0,circular:!0,selfJoin:!1}),R(ui,"defaultRoutes",{backgroundColor:"backgroundColor"}),R(ui,"descriptors",{_scriptable:!0,_indexable:n=>n!=="borderDash"});function Vg(e,t,n=t){e.lineCap=B(n.borderCapStyle,t.borderCapStyle),e.setLineDash(B(n.borderDash,t.borderDash)),e.lineDashOffset=B(n.borderDashOffset,t.borderDashOffset),e.lineJoin=B(n.borderJoinStyle,t.borderJoinStyle),e.lineWidth=B(n.borderWidth,t.borderWidth),e.strokeStyle=B(n.borderColor,t.borderColor)}function Vw(e,t,n){e.lineTo(n.x,n.y)}function Uw(e){return e.stepped?Sb:e.tension||e.cubicInterpolationMode==="monotone"?Nb:Vw}function Ug(e,t,n={}){const r=e.length,{start:i=0,end:s=r-1}=n,{start:a,end:o}=t,l=Math.max(i,a),u=Math.min(s,o),d=i<a&&s<a||i>o&&s>o;return{count:r,start:l,loop:t.loop,ilen:u<l&&!d?r+u-l:u-l}}function Yw(e,t,n,r){const{points:i,options:s}=t,{count:a,start:o,loop:l,ilen:u}=Ug(i,n,r),d=Uw(s);let{move:h=!0,reverse:f}=r||{},p,m,v;for(p=0;p<=u;++p)m=i[(o+(f?u-p:p))%a],!m.skip&&(h?(e.moveTo(m.x,m.y),h=!1):d(e,v,m,f,s.stepped),v=m);return l&&(m=i[(o+(f?u:0))%a],d(e,v,m,f,s.stepped)),!!l}function Xw(e,t,n,r){const i=t.points,{count:s,start:a,ilen:o}=Ug(i,n,r),{move:l=!0,reverse:u}=r||{};let d=0,h=0,f,p,m,v,y,g;const x=k=>(a+(u?o-k:k))%s,b=()=>{v!==y&&(e.lineTo(d,y),e.lineTo(d,v),e.lineTo(d,g))};for(l&&(p=i[x(0)],e.moveTo(p.x,p.y)),f=0;f<=o;++f){if(p=i[x(f)],p.skip)continue;const k=p.x,w=p.y,j=k|0;j===m?(w<v?v=w:w>y&&(y=w),d=(h*d+k)/++h):(b(),e.lineTo(k,w),m=j,h=0,v=y=w),g=w}b()}function dc(e){const t=e.options,n=t.borderDash&&t.borderDash.length;return!e._decimated&&!e._loop&&!t.tension&&t.cubicInterpolationMode!=="monotone"&&!t.stepped&&!n?Xw:Yw}function Kw(e){return e.stepped?ik:e.tension||e.cubicInterpolationMode==="monotone"?sk:Mn}function Qw(e,t,n,r){let i=t._path;i||(i=t._path=new Path2D,t.path(i,n,r)&&i.closePath()),Vg(e,t.options),e.stroke(i)}function Gw(e,t,n,r){const{segments:i,options:s}=t,a=dc(t);for(const o of i)Vg(e,s,o.style),e.beginPath(),a(e,t,o,{start:n,end:n+r-1})&&e.closePath(),e.stroke()}const Zw=typeof Path2D=="function";function qw(e,t,n,r){Zw&&!t.options.segment?Qw(e,t,n,r):Gw(e,t,n,r)}class nn extends vt{constructor(t){super(),this.animated=!0,this.options=void 0,this._chart=void 0,this._loop=void 0,this._fullLoop=void 0,this._path=void 0,this._points=void 0,this._segments=void 0,this._decimated=!1,this._pointsUpdated=!1,this._datasetIndex=void 0,t&&Object.assign(this,t)}updateControlPoints(t,n){const r=this.options;if((r.tension||r.cubicInterpolationMode==="monotone")&&!r.stepped&&!this._pointsUpdated){const i=r.spanGaps?this._loop:this._fullLoop;Gb(this._points,r,t,i,n),this._pointsUpdated=!0}}set points(t){this._points=t,delete this._segments,delete this._path,this._pointsUpdated=!1}get points(){return this._points}get segments(){return this._segments||(this._segments=dk(this,this.options.segment))}first(){const t=this.segments,n=this.points;return t.length&&n[t[0].start]}last(){const t=this.segments,n=this.points,r=t.length;return r&&n[t[r-1].end]}interpolate(t,n){const r=this.options,i=t[n],s=this.points,a=Tg(this,{property:n,start:i,end:i});if(!a.length)return;const o=[],l=Kw(r);let u,d;for(u=0,d=a.length;u<d;++u){const{start:h,end:f}=a[u],p=s[h],m=s[f];if(p===m){o.push(p);continue}const v=Math.abs((i-p[n])/(m[n]-p[n])),y=l(p,m,v,r.stepped);y[n]=t[n],o.push(y)}return o.length===1?o[0]:o}pathSegment(t,n,r){return dc(this)(t,this,n,r)}path(t,n,r){const i=this.segments,s=dc(this);let a=this._loop;n=n||0,r=r||this.points.length-n;for(const o of i)a&=s(t,this,o,{start:n,end:n+r-1});return!!a}draw(t,n,r,i){const s=this.options||{};(this.points||[]).length&&s.borderWidth&&(t.save(),qw(t,this,r,i),t.restore()),this.animated&&(this._pointsUpdated=!1,this._path=void 0)}}R(nn,"id","line"),R(nn,"defaults",{borderCapStyle:"butt",borderDash:[],borderDashOffset:0,borderJoinStyle:"miter",borderWidth:3,capBezierPoints:!0,cubicInterpolationMode:"default",fill:!1,spanGaps:!1,stepped:!1,tension:0}),R(nn,"defaultRoutes",{backgroundColor:"backgroundColor",borderColor:"borderColor"}),R(nn,"descriptors",{_scriptable:!0,_indexable:t=>t!=="borderDash"&&t!=="fill"});function Kh(e,t,n,r){const i=e.options,{[n]:s}=e.getProps([n],r);return Math.abs(t-s)<i.radius+i.hitRadius}class aa extends vt{constructor(n){super();R(this,"parsed");R(this,"skip");R(this,"stop");this.options=void 0,this.parsed=void 0,this.skip=void 0,this.stop=void 0,n&&Object.assign(this,n)}inRange(n,r,i){const s=this.options,{x:a,y:o}=this.getProps(["x","y"],i);return Math.pow(n-a,2)+Math.pow(r-o,2)<Math.pow(s.hitRadius+s.radius,2)}inXRange(n,r){return Kh(this,n,"x",r)}inYRange(n,r){return Kh(this,n,"y",r)}getCenterPoint(n){const{x:r,y:i}=this.getProps(["x","y"],n);return{x:r,y:i}}size(n){n=n||this.options||{};let r=n.radius||0;r=Math.max(r,r&&n.hoverRadius||0);const i=r&&n.borderWidth||0;return(r+i)*2}draw(n,r){const i=this.options;this.skip||i.radius<.1||!Zi(this,r,this.size(i)/2)||(n.strokeStyle=i.borderColor,n.lineWidth=i.borderWidth,n.fillStyle=i.backgroundColor,lc(n,i,this.x,this.y))}getRange(){const n=this.options||{};return n.radius+n.hitRadius}}R(aa,"id","point"),R(aa,"defaults",{borderWidth:1,hitRadius:1,hoverBorderWidth:1,hoverRadius:4,pointStyle:"circle",radius:3,rotation:0}),R(aa,"defaultRoutes",{backgroundColor:"backgroundColor",borderColor:"borderColor"});function Yg(e,t){const{x:n,y:r,base:i,width:s,height:a}=e.getProps(["x","y","base","width","height"],t);let o,l,u,d,h;return e.horizontal?(h=a/2,o=Math.min(n,i),l=Math.max(n,i),u=r-h,d=r+h):(h=s/2,o=n-h,l=n+h,u=Math.min(r,i),d=Math.max(r,i)),{left:o,top:u,right:l,bottom:d}}function rn(e,t,n,r){return e?0:Pe(t,n,r)}function Jw(e,t,n){const r=e.options.borderWidth,i=e.borderSkipped,s=kg(r);return{t:rn(i.top,s.top,0,n),r:rn(i.right,s.right,0,t),b:rn(i.bottom,s.bottom,0,n),l:rn(i.left,s.left,0,t)}}function e_(e,t,n){const{enableBorderRadius:r}=e.getProps(["enableBorderRadius"]),i=e.options.borderRadius,s=wr(i),a=Math.min(t,n),o=e.borderSkipped,l=r||$(i);return{topLeft:rn(!l||o.top||o.left,s.topLeft,0,a),topRight:rn(!l||o.top||o.right,s.topRight,0,a),bottomLeft:rn(!l||o.bottom||o.left,s.bottomLeft,0,a),bottomRight:rn(!l||o.bottom||o.right,s.bottomRight,0,a)}}function t_(e){const t=Yg(e),n=t.right-t.left,r=t.bottom-t.top,i=Jw(e,n/2,r/2),s=e_(e,n/2,r/2);return{outer:{x:t.left,y:t.top,w:n,h:r,radius:s},inner:{x:t.left+i.l,y:t.top+i.t,w:n-i.l-i.r,h:r-i.t-i.b,radius:{topLeft:Math.max(0,s.topLeft-Math.max(i.t,i.l)),topRight:Math.max(0,s.topRight-Math.max(i.t,i.r)),bottomLeft:Math.max(0,s.bottomLeft-Math.max(i.b,i.l)),bottomRight:Math.max(0,s.bottomRight-Math.max(i.b,i.r))}}}}function rl(e,t,n,r){const i=t===null,s=n===null,o=e&&!(i&&s)&&Yg(e,r);return o&&(i||At(t,o.left,o.right))&&(s||At(n,o.top,o.bottom))}function n_(e){return e.topLeft||e.topRight||e.bottomLeft||e.bottomRight}function r_(e,t){e.rect(t.x,t.y,t.w,t.h)}function il(e,t,n={}){const r=e.x!==n.x?-t:0,i=e.y!==n.y?-t:0,s=(e.x+e.w!==n.x+n.w?t:0)-r,a=(e.y+e.h!==n.y+n.h?t:0)-i;return{x:e.x+r,y:e.y+i,w:e.w+s,h:e.h+a,radius:e.radius}}class oa extends vt{constructor(t){super(),this.options=void 0,this.horizontal=void 0,this.base=void 0,this.width=void 0,this.height=void 0,this.inflateAmount=void 0,t&&Object.assign(this,t)}draw(t){const{inflateAmount:n,options:{borderColor:r,backgroundColor:i}}=this,{inner:s,outer:a}=t_(this),o=n_(a.radius)?Fa:r_;t.save(),(a.w!==s.w||a.h!==s.h)&&(t.beginPath(),o(t,il(a,n,s)),t.clip(),o(t,il(s,-n,a)),t.fillStyle=r,t.fill("evenodd")),t.beginPath(),o(t,il(s,n)),t.fillStyle=i,t.fill(),t.restore()}inRange(t,n,r){return rl(this,t,n,r)}inXRange(t,n){return rl(this,t,null,n)}inYRange(t,n){return rl(this,null,t,n)}getCenterPoint(t){const{x:n,y:r,base:i,horizontal:s}=this.getProps(["x","y","base","horizontal"],t);return{x:s?(n+i)/2:n,y:s?r:(r+i)/2}}getRange(t){return t==="x"?this.width/2:this.height/2}}R(oa,"id","bar"),R(oa,"defaults",{borderSkipped:"start",borderWidth:0,borderRadius:0,inflateAmount:"auto",pointStyle:void 0}),R(oa,"defaultRoutes",{backgroundColor:"backgroundColor",borderColor:"borderColor"});function i_(e,t,n){const r=e.segments,i=e.points,s=t.points,a=[];for(const o of r){let{start:l,end:u}=o;u=mo(l,u,i);const d=hc(n,i[l],i[u],o.loop);if(!t.segments){a.push({source:o,target:d,start:i[l],end:i[u]});continue}const h=Tg(t,d);for(const f of h){const p=hc(n,s[f.start],s[f.end],f.loop),m=Eg(o,i,p);for(const v of m)a.push({source:v,target:f,start:{[n]:Qh(d,p,"start",Math.max)},end:{[n]:Qh(d,p,"end",Math.min)}})}}return a}function hc(e,t,n,r){if(r)return;let i=t[e],s=n[e];return e==="angle"&&(i=Qe(i),s=Qe(s)),{property:e,start:i,end:s}}function s_(e,t){const{x:n=null,y:r=null}=e||{},i=t.points,s=[];return t.segments.forEach(({start:a,end:o})=>{o=mo(a,o,i);const l=i[a],u=i[o];r!==null?(s.push({x:l.x,y:r}),s.push({x:u.x,y:r})):n!==null&&(s.push({x:n,y:l.y}),s.push({x:n,y:u.y}))}),s}function mo(e,t,n){for(;t>e;t--){const r=n[t];if(!isNaN(r.x)&&!isNaN(r.y))break}return t}function Qh(e,t,n,r){return e&&t?r(e[n],t[n]):e?e[n]:t?t[n]:0}function Xg(e,t){let n=[],r=!1;return pe(e)?(r=!0,n=e):n=s_(e,t),n.length?new nn({points:n,options:{tension:0},_loop:r,_fullLoop:r}):null}function Gh(e){return e&&e.fill!==!1}function a_(e,t,n){let i=e[t].fill;const s=[t];let a;if(!n)return i;for(;i!==!1&&s.indexOf(i)===-1;){if(!De(i))return i;if(a=e[i],!a)return!1;if(a.visible)return i;s.push(i),i=a.fill}return!1}function o_(e,t,n){const r=d_(e);if($(r))return isNaN(r.value)?!1:r;let i=parseFloat(r);return De(i)&&Math.floor(i)===i?l_(r[0],t,i,n):["origin","start","end","stack","shape"].indexOf(r)>=0&&r}function l_(e,t,n,r){return(e==="-"||e==="+")&&(n=t+n),n===t||n<0||n>=r?!1:n}function c_(e,t){let n=null;return e==="start"?n=t.bottom:e==="end"?n=t.top:$(e)?n=t.getPixelForValue(e.value):t.getBasePixel&&(n=t.getBasePixel()),n}function u_(e,t,n){let r;return e==="start"?r=n:e==="end"?r=t.options.reverse?t.min:t.max:$(e)?r=e.value:r=t.getBaseValue(),r}function d_(e){const t=e.options,n=t.fill;let r=B(n&&n.target,n);return r===void 0&&(r=!!t.backgroundColor),r===!1||r===null?!1:r===!0?"origin":r}function h_(e){const{scale:t,index:n,line:r}=e,i=[],s=r.segments,a=r.points,o=f_(t,n);o.push(Xg({x:null,y:t.bottom},r));for(let l=0;l<s.length;l++){const u=s[l];for(let d=u.start;d<=u.end;d++)p_(i,a[d],o)}return new nn({points:i,options:{}})}function f_(e,t){const n=[],r=e.getMatchingVisibleMetas("line");for(let i=0;i<r.length;i++){const s=r[i];if(s.index===t)break;s.hidden||n.unshift(s.dataset)}return n}function p_(e,t,n){const r=[];for(let i=0;i<n.length;i++){const s=n[i],{first:a,last:o,point:l}=m_(s,t,"x");if(!(!l||a&&o)){if(a)r.unshift(l);else if(e.push(l),!o)break}}e.push(...r)}function m_(e,t,n){const r=e.interpolate(t,n);if(!r)return{};const i=r[n],s=e.segments,a=e.points;let o=!1,l=!1;for(let u=0;u<s.length;u++){const d=s[u],h=a[d.start][n],f=a[d.end][n];if(At(i,h,f)){o=i===h,l=i===f;break}}return{first:o,last:l,point:r}}class Kg{constructor(t){this.x=t.x,this.y=t.y,this.radius=t.radius}pathSegment(t,n,r){const{x:i,y:s,radius:a}=this;return n=n||{start:0,end:be},t.arc(i,s,a,n.end,n.start,!0),!r.bounds}interpolate(t){const{x:n,y:r,radius:i}=this,s=t.angle;return{x:n+Math.cos(s)*i,y:r+Math.sin(s)*i,angle:s}}}function g_(e){const{chart:t,fill:n,line:r}=e;if(De(n))return v_(t,n);if(n==="stack")return h_(e);if(n==="shape")return!0;const i=y_(e);return i instanceof Kg?i:Xg(i,r)}function v_(e,t){const n=e.getDatasetMeta(t);return n&&e.isDatasetVisible(t)?n.dataset:null}function y_(e){return(e.scale||{}).getPointPositionForValue?b_(e):x_(e)}function x_(e){const{scale:t={},fill:n}=e,r=c_(n,t);if(De(r)){const i=t.isHorizontal();return{x:i?r:null,y:i?null:r}}return null}function b_(e){const{scale:t,fill:n}=e,r=t.options,i=t.getLabels().length,s=r.reverse?t.max:t.min,a=u_(n,t,s),o=[];if(r.grid.circular){const l=t.getPointPositionForValue(0,s);return new Kg({x:l.x,y:l.y,radius:t.getDistanceFromCenterForValue(a)})}for(let l=0;l<i;++l)o.push(t.getPointPositionForValue(l,a));return o}function sl(e,t,n){const r=g_(t),{chart:i,index:s,line:a,scale:o,axis:l}=t,u=a.options,d=u.fill,h=u.backgroundColor,{above:f=h,below:p=h}=d||{},m=i.getDatasetMeta(s),v=zg(i,m);r&&a.points.length&&(uo(e,n),k_(e,{line:a,target:r,above:f,below:p,area:n,scale:o,axis:l,clip:v}),ho(e))}function k_(e,t){const{line:n,target:r,above:i,below:s,area:a,scale:o,clip:l}=t,u=n._loop?"angle":t.axis;e.save();let d=s;s!==i&&(u==="x"?(Zh(e,r,a.top),al(e,{line:n,target:r,color:i,scale:o,property:u,clip:l}),e.restore(),e.save(),Zh(e,r,a.bottom)):u==="y"&&(qh(e,r,a.left),al(e,{line:n,target:r,color:s,scale:o,property:u,clip:l}),e.restore(),e.save(),qh(e,r,a.right),d=i)),al(e,{line:n,target:r,color:d,scale:o,property:u,clip:l}),e.restore()}function Zh(e,t,n){const{segments:r,points:i}=t;let s=!0,a=!1;e.beginPath();for(const o of r){const{start:l,end:u}=o,d=i[l],h=i[mo(l,u,i)];s?(e.moveTo(d.x,d.y),s=!1):(e.lineTo(d.x,n),e.lineTo(d.x,d.y)),a=!!t.pathSegment(e,o,{move:a}),a?e.closePath():e.lineTo(h.x,n)}e.lineTo(t.first().x,n),e.closePath(),e.clip()}function qh(e,t,n){const{segments:r,points:i}=t;let s=!0,a=!1;e.beginPath();for(const o of r){const{start:l,end:u}=o,d=i[l],h=i[mo(l,u,i)];s?(e.moveTo(d.x,d.y),s=!1):(e.lineTo(n,d.y),e.lineTo(d.x,d.y)),a=!!t.pathSegment(e,o,{move:a}),a?e.closePath():e.lineTo(n,h.y)}e.lineTo(n,t.first().y),e.closePath(),e.clip()}function al(e,t){const{line:n,target:r,property:i,color:s,scale:a,clip:o}=t,l=i_(n,r,i);for(const{source:u,target:d,start:h,end:f}of l){const{style:{backgroundColor:p=s}={}}=u,m=r!==!0;e.save(),e.fillStyle=p,w_(e,a,o,m&&hc(i,h,f)),e.beginPath();const v=!!n.pathSegment(e,u);let y;if(m){v?e.closePath():Jh(e,r,f,i);const g=!!r.pathSegment(e,d,{move:v,reverse:!0});y=v&&g,y||Jh(e,r,h,i)}e.closePath(),e.fill(y?"evenodd":"nonzero"),e.restore()}}function w_(e,t,n,r){const i=t.chart.chartArea,{property:s,start:a,end:o}=r||{};if(s==="x"||s==="y"){let l,u,d,h;s==="x"?(l=a,u=i.top,d=o,h=i.bottom):(l=i.left,u=a,d=i.right,h=o),e.beginPath(),n&&(l=Math.max(l,n.left),d=Math.min(d,n.right),u=Math.max(u,n.top),h=Math.min(h,n.bottom)),e.rect(l,u,d-l,h-u),e.clip()}}function Jh(e,t,n,r){const i=t.interpolate(n,r);i&&e.lineTo(i.x,i.y)}var __={id:"filler",afterDatasetsUpdate(e,t,n){const r=(e.data.datasets||[]).length,i=[];let s,a,o,l;for(a=0;a<r;++a)s=e.getDatasetMeta(a),o=s.dataset,l=null,o&&o.options&&o instanceof nn&&(l={visible:e.isDatasetVisible(a),index:a,fill:o_(o,a,r),chart:e,axis:s.controller.options.indexAxis,scale:s.vScale,line:o}),s.$filler=l,i.push(l);for(a=0;a<r;++a)l=i[a],!(!l||l.fill===!1)&&(l.fill=a_(i,a,n.propagate))},beforeDraw(e,t,n){const r=n.drawTime==="beforeDraw",i=e.getSortedVisibleDatasetMetas(),s=e.chartArea;for(let a=i.length-1;a>=0;--a){const o=i[a].$filler;o&&(o.line.updateControlPoints(s,o.axis),r&&o.fill&&sl(e.ctx,o,s))}},beforeDatasetsDraw(e,t,n){if(n.drawTime!=="beforeDatasetsDraw")return;const r=e.getSortedVisibleDatasetMetas();for(let i=r.length-1;i>=0;--i){const s=r[i].$filler;Gh(s)&&sl(e.ctx,s,e.chartArea)}},beforeDatasetDraw(e,t,n){const r=t.meta.$filler;!Gh(r)||n.drawTime!=="beforeDatasetDraw"||sl(e.ctx,r,e.chartArea)},defaults:{propagate:!0,drawTime:"beforeDatasetDraw"}};const ef=(e,t)=>{let{boxHeight:n=t,boxWidth:r=t}=e;return e.usePointStyle&&(n=Math.min(n,t),r=e.pointStyleWidth||Math.min(r,t)),{boxWidth:r,boxHeight:n,itemHeight:Math.max(t,n)}},j_=(e,t)=>e!==null&&t!==null&&e.datasetIndex===t.datasetIndex&&e.index===t.index;class tf extends vt{constructor(t){super(),this._added=!1,this.legendHitBoxes=[],this._hoveredItem=null,this.doughnutMode=!1,this.chart=t.chart,this.options=t.options,this.ctx=t.ctx,this.legendItems=void 0,this.columnSizes=void 0,this.lineWidths=void 0,this.maxHeight=void 0,this.maxWidth=void 0,this.top=void 0,this.bottom=void 0,this.left=void 0,this.right=void 0,this.height=void 0,this.width=void 0,this._margins=void 0,this.position=void 0,this.weight=void 0,this.fullSize=void 0}update(t,n,r){this.maxWidth=t,this.maxHeight=n,this._margins=r,this.setDimensions(),this.buildLabels(),this.fit()}setDimensions(){this.isHorizontal()?(this.width=this.maxWidth,this.left=this._margins.left,this.right=this.width):(this.height=this.maxHeight,this.top=this._margins.top,this.bottom=this.height)}buildLabels(){const t=this.options.labels||{};let n=te(t.generateLabels,[this.chart],this)||[];t.filter&&(n=n.filter(r=>t.filter(r,this.chart.data))),t.sort&&(n=n.sort((r,i)=>t.sort(r,i,this.chart.data))),this.options.reverse&&n.reverse(),this.legendItems=n}fit(){const{options:t,ctx:n}=this;if(!t.display){this.width=this.height=0;return}const r=t.labels,i=Ee(r.font),s=i.size,a=this._computeTitleHeight(),{boxWidth:o,itemHeight:l}=ef(r,s);let u,d;n.font=i.string,this.isHorizontal()?(u=this.maxWidth,d=this._fitRows(a,s,o,l)+10):(d=this.maxHeight,u=this._fitCols(a,i,o,l)+10),this.width=Math.min(u,t.maxWidth||this.maxWidth),this.height=Math.min(d,t.maxHeight||this.maxHeight)}_fitRows(t,n,r,i){const{ctx:s,maxWidth:a,options:{labels:{padding:o}}}=this,l=this.legendHitBoxes=[],u=this.lineWidths=[0],d=i+o;let h=t;s.textAlign="left",s.textBaseline="middle";let f=-1,p=-d;return this.legendItems.forEach((m,v)=>{const y=r+n/2+s.measureText(m.text).width;(v===0||u[u.length-1]+y+2*o>a)&&(h+=d,u[u.length-(v>0?0:1)]=0,p+=d,f++),l[v]={left:0,top:p,row:f,width:y,height:i},u[u.length-1]+=y+o}),h}_fitCols(t,n,r,i){const{ctx:s,maxHeight:a,options:{labels:{padding:o}}}=this,l=this.legendHitBoxes=[],u=this.columnSizes=[],d=a-t;let h=o,f=0,p=0,m=0,v=0;return this.legendItems.forEach((y,g)=>{const{itemWidth:x,itemHeight:b}=S_(r,n,s,y,i);g>0&&p+b+2*o>d&&(h+=f+o,u.push({width:f,height:p}),m+=f+o,v++,f=p=0),l[g]={left:m,top:p,col:v,width:x,height:b},f=Math.max(f,x),p+=b+o}),h+=f,u.push({width:f,height:p}),h}adjustHitBoxes(){if(!this.options.display)return;const t=this._computeTitleHeight(),{legendHitBoxes:n,options:{align:r,labels:{padding:i},rtl:s}}=this,a=_r(s,this.left,this.width);if(this.isHorizontal()){let o=0,l=Ce(r,this.left+i,this.right-this.lineWidths[o]);for(const u of n)o!==u.row&&(o=u.row,l=Ce(r,this.left+i,this.right-this.lineWidths[o])),u.top+=this.top+t+i,u.left=a.leftForLtr(a.x(l),u.width),l+=u.width+i}else{let o=0,l=Ce(r,this.top+t+i,this.bottom-this.columnSizes[o].height);for(const u of n)u.col!==o&&(o=u.col,l=Ce(r,this.top+t+i,this.bottom-this.columnSizes[o].height)),u.top=l,u.left+=this.left+i,u.left=a.leftForLtr(a.x(u.left),u.width),l+=u.height+i}}isHorizontal(){return this.options.position==="top"||this.options.position==="bottom"}draw(){if(this.options.display){const t=this.ctx;uo(t,this),this._draw(),ho(t)}}_draw(){const{options:t,columnSizes:n,lineWidths:r,ctx:i}=this,{align:s,labels:a}=t,o=ue.color,l=_r(t.rtl,this.left,this.width),u=Ee(a.font),{padding:d}=a,h=u.size,f=h/2;let p;this.drawTitle(),i.textAlign=l.textAlign("left"),i.textBaseline="middle",i.lineWidth=.5,i.font=u.string;const{boxWidth:m,boxHeight:v,itemHeight:y}=ef(a,h),g=function(j,S,N){if(isNaN(m)||m<=0||isNaN(v)||v<0)return;i.save();const T=B(N.lineWidth,1);if(i.fillStyle=B(N.fillStyle,o),i.lineCap=B(N.lineCap,"butt"),i.lineDashOffset=B(N.lineDashOffset,0),i.lineJoin=B(N.lineJoin,"miter"),i.lineWidth=T,i.strokeStyle=B(N.strokeStyle,o),i.setLineDash(B(N.lineDash,[])),a.usePointStyle){const E={radius:v*Math.SQRT2/2,pointStyle:N.pointStyle,rotation:N.rotation,borderWidth:T},L=l.xPlus(j,m/2),A=S+f;bg(i,E,L,A,a.pointStyleWidth&&m)}else{const E=S+Math.max((h-v)/2,0),L=l.leftForLtr(j,m),A=wr(N.borderRadius);i.beginPath(),Object.values(A).some(q=>q!==0)?Fa(i,{x:L,y:E,w:m,h:v,radius:A}):i.rect(L,E,m,v),i.fill(),T!==0&&i.stroke()}i.restore()},x=function(j,S,N){qi(i,N.text,j,S+y/2,u,{strikethrough:N.hidden,textAlign:l.textAlign(N.textAlign)})},b=this.isHorizontal(),k=this._computeTitleHeight();b?p={x:Ce(s,this.left+d,this.right-r[0]),y:this.top+d+k,line:0}:p={x:this.left+d,y:Ce(s,this.top+k+d,this.bottom-n[0].height),line:0},Cg(this.ctx,t.textDirection);const w=y+d;this.legendItems.forEach((j,S)=>{i.strokeStyle=j.fontColor,i.fillStyle=j.fontColor;const N=i.measureText(j.text).width,T=l.textAlign(j.textAlign||(j.textAlign=a.textAlign)),E=m+f+N;let L=p.x,A=p.y;l.setWidth(this.width),b?S>0&&L+E+d>this.right&&(A=p.y+=w,p.line++,L=p.x=Ce(s,this.left+d,this.right-r[p.line])):S>0&&A+w>this.bottom&&(L=p.x=L+n[p.line].width+d,p.line++,A=p.y=Ce(s,this.top+k+d,this.bottom-n[p.line].height));const q=l.x(L);if(g(q,A,j),L=hb(T,L+m+f,b?L+E:this.right,t.rtl),x(l.x(L),A,j),b)p.x+=E+d;else if(typeof j.text!="string"){const ve=u.lineHeight;p.y+=Qg(j,ve)+d}else p.y+=w}),Mg(this.ctx,t.textDirection)}drawTitle(){const t=this.options,n=t.title,r=Ee(n.font),i=ct(n.padding);if(!n.display)return;const s=_r(t.rtl,this.left,this.width),a=this.ctx,o=n.position,l=r.size/2,u=i.top+l;let d,h=this.left,f=this.width;if(this.isHorizontal())f=Math.max(...this.lineWidths),d=this.top+u,h=Ce(t.align,h,this.right-f);else{const m=this.columnSizes.reduce((v,y)=>Math.max(v,y.height),0);d=u+Ce(t.align,this.top,this.bottom-m-t.labels.padding-this._computeTitleHeight())}const p=Ce(o,h,h+f);a.textAlign=s.textAlign(_u(o)),a.textBaseline="middle",a.strokeStyle=n.color,a.fillStyle=n.color,a.font=r.string,qi(a,n.text,p,d,r)}_computeTitleHeight(){const t=this.options.title,n=Ee(t.font),r=ct(t.padding);return t.display?n.lineHeight+r.height:0}_getLegendItemAt(t,n){let r,i,s;if(At(t,this.left,this.right)&&At(n,this.top,this.bottom)){for(s=this.legendHitBoxes,r=0;r<s.length;++r)if(i=s[r],At(t,i.left,i.left+i.width)&&At(n,i.top,i.top+i.height))return this.legendItems[r]}return null}handleEvent(t){const n=this.options;if(!M_(t.type,n))return;const r=this._getLegendItemAt(t.x,t.y);if(t.type==="mousemove"||t.type==="mouseout"){const i=this._hoveredItem,s=j_(i,r);i&&!s&&te(n.onLeave,[t,i,this],this),this._hoveredItem=r,r&&!s&&te(n.onHover,[t,r,this],this)}else r&&te(n.onClick,[t,r,this],this)}}function S_(e,t,n,r,i){const s=N_(r,e,t,n),a=C_(i,r,t.lineHeight);return{itemWidth:s,itemHeight:a}}function N_(e,t,n,r){let i=e.text;return i&&typeof i!="string"&&(i=i.reduce((s,a)=>s.length>a.length?s:a)),t+n.size/2+r.measureText(i).width}function C_(e,t,n){let r=e;return typeof t.text!="string"&&(r=Qg(t,n)),r}function Qg(e,t){const n=e.text?e.text.length:0;return t*n}function M_(e,t){return!!((e==="mousemove"||e==="mouseout")&&(t.onHover||t.onLeave)||t.onClick&&(e==="click"||e==="mouseup"))}var zu={id:"legend",_element:tf,start(e,t,n){const r=e.legend=new tf({ctx:e.ctx,options:n,chart:e});st.configure(e,r,n),st.addBox(e,r)},stop(e){st.removeBox(e,e.legend),delete e.legend},beforeUpdate(e,t,n){const r=e.legend;st.configure(e,r,n),r.options=n},afterUpdate(e){const t=e.legend;t.buildLabels(),t.adjustHitBoxes()},afterEvent(e,t){t.replay||e.legend.handleEvent(t.event)},defaults:{display:!0,position:"top",align:"center",fullSize:!0,reverse:!1,weight:1e3,onClick(e,t,n){const r=t.datasetIndex,i=n.chart;i.isDatasetVisible(r)?(i.hide(r),t.hidden=!0):(i.show(r),t.hidden=!1)},onHover:null,onLeave:null,labels:{color:e=>e.chart.options.color,boxWidth:40,padding:10,generateLabels(e){const t=e.data.datasets,{labels:{usePointStyle:n,pointStyle:r,textAlign:i,color:s,useBorderRadius:a,borderRadius:o}}=e.legend.options;return e._getSortedDatasetMetas().map(l=>{const u=l.controller.getStyle(n?0:void 0),d=ct(u.borderWidth);return{text:t[l.index].label,fillStyle:u.backgroundColor,fontColor:s,hidden:!l.visible,lineCap:u.borderCapStyle,lineDash:u.borderDash,lineDashOffset:u.borderDashOffset,lineJoin:u.borderJoinStyle,lineWidth:(d.width+d.height)/4,strokeStyle:u.borderColor,pointStyle:r||u.pointStyle,rotation:u.rotation,textAlign:i||u.textAlign,borderRadius:a&&(o||u.borderRadius),datasetIndex:l.index}},this)}},title:{color:e=>e.chart.options.color,display:!1,position:"center",text:""}},descriptors:{_scriptable:e=>!e.startsWith("on"),labels:{_scriptable:e=>!["generateLabels","filter","sort"].includes(e)}}};class Gg extends vt{constructor(t){super(),this.chart=t.chart,this.options=t.options,this.ctx=t.ctx,this._padding=void 0,this.top=void 0,this.bottom=void 0,this.left=void 0,this.right=void 0,this.width=void 0,this.height=void 0,this.position=void 0,this.weight=void 0,this.fullSize=void 0}update(t,n){const r=this.options;if(this.left=0,this.top=0,!r.display){this.width=this.height=this.right=this.bottom=0;return}this.width=this.right=t,this.height=this.bottom=n;const i=pe(r.text)?r.text.length:1;this._padding=ct(r.padding);const s=i*Ee(r.font).lineHeight+this._padding.height;this.isHorizontal()?this.height=s:this.width=s}isHorizontal(){const t=this.options.position;return t==="top"||t==="bottom"}_drawArgs(t){const{top:n,left:r,bottom:i,right:s,options:a}=this,o=a.align;let l=0,u,d,h;return this.isHorizontal()?(d=Ce(o,r,s),h=n+t,u=s-r):(a.position==="left"?(d=r+t,h=Ce(o,i,n),l=Q*-.5):(d=s-t,h=Ce(o,n,i),l=Q*.5),u=i-n),{titleX:d,titleY:h,maxWidth:u,rotation:l}}draw(){const t=this.ctx,n=this.options;if(!n.display)return;const r=Ee(n.font),s=r.lineHeight/2+this._padding.top,{titleX:a,titleY:o,maxWidth:l,rotation:u}=this._drawArgs(s);qi(t,n.text,0,0,r,{color:n.color,maxWidth:l,rotation:u,textAlign:_u(n.align),textBaseline:"middle",translation:[a,o]})}}function P_(e,t){const n=new Gg({ctx:e.ctx,options:t,chart:e});st.configure(e,n,t),st.addBox(e,n),e.titleBlock=n}var Zg={id:"title",_element:Gg,start(e,t,n){P_(e,n)},stop(e){const t=e.titleBlock;st.removeBox(e,t),delete e.titleBlock},beforeUpdate(e,t,n){const r=e.titleBlock;st.configure(e,r,n),r.options=n},defaults:{align:"center",display:!1,font:{weight:"bold"},fullSize:!0,padding:10,position:"top",text:"",weight:2e3},defaultRoutes:{color:"color"},descriptors:{_scriptable:!0,_indexable:!1}};const di={average(e){if(!e.length)return!1;let t,n,r=new Set,i=0,s=0;for(t=0,n=e.length;t<n;++t){const o=e[t].element;if(o&&o.hasValue()){const l=o.tooltipPosition();r.add(l.x),i+=l.y,++s}}return s===0||r.size===0?!1:{x:[...r].reduce((o,l)=>o+l)/r.size,y:i/s}},nearest(e,t){if(!e.length)return!1;let n=t.x,r=t.y,i=Number.POSITIVE_INFINITY,s,a,o;for(s=0,a=e.length;s<a;++s){const l=e[s].element;if(l&&l.hasValue()){const u=l.getCenterPoint(),d=ac(t,u);d<i&&(i=d,o=l)}}if(o){const l=o.tooltipPosition();n=l.x,r=l.y}return{x:n,y:r}}};function kt(e,t){return t&&(pe(t)?Array.prototype.push.apply(e,t):e.push(t)),e}function Tt(e){return(typeof e=="string"||e instanceof String)&&e.indexOf(`
`)>-1?e.split(`
`):e}function E_(e,t){const{element:n,datasetIndex:r,index:i}=t,s=e.getDatasetMeta(r).controller,{label:a,value:o}=s.getLabelAndValue(i);return{chart:e,label:a,parsed:s.getParsed(i),raw:e.data.datasets[r].data[i],formattedValue:o,dataset:s.getDataset(),dataIndex:i,datasetIndex:r,element:n}}function nf(e,t){const n=e.chart.ctx,{body:r,footer:i,title:s}=e,{boxWidth:a,boxHeight:o}=t,l=Ee(t.bodyFont),u=Ee(t.titleFont),d=Ee(t.footerFont),h=s.length,f=i.length,p=r.length,m=ct(t.padding);let v=m.height,y=0,g=r.reduce((k,w)=>k+w.before.length+w.lines.length+w.after.length,0);if(g+=e.beforeBody.length+e.afterBody.length,h&&(v+=h*u.lineHeight+(h-1)*t.titleSpacing+t.titleMarginBottom),g){const k=t.displayColors?Math.max(o,l.lineHeight):l.lineHeight;v+=p*k+(g-p)*l.lineHeight+(g-1)*t.bodySpacing}f&&(v+=t.footerMarginTop+f*d.lineHeight+(f-1)*t.footerSpacing);let x=0;const b=function(k){y=Math.max(y,n.measureText(k).width+x)};return n.save(),n.font=u.string,Y(e.title,b),n.font=l.string,Y(e.beforeBody.concat(e.afterBody),b),x=t.displayColors?a+2+t.boxPadding:0,Y(r,k=>{Y(k.before,b),Y(k.lines,b),Y(k.after,b)}),x=0,n.font=d.string,Y(e.footer,b),n.restore(),y+=m.width,{width:y,height:v}}function T_(e,t){const{y:n,height:r}=t;return n<r/2?"top":n>e.height-r/2?"bottom":"center"}function z_(e,t,n,r){const{x:i,width:s}=r,a=n.caretSize+n.caretPadding;if(e==="left"&&i+s+a>t.width||e==="right"&&i-s-a<0)return!0}function D_(e,t,n,r){const{x:i,width:s}=n,{width:a,chartArea:{left:o,right:l}}=e;let u="center";return r==="center"?u=i<=(o+l)/2?"left":"right":i<=s/2?u="left":i>=a-s/2&&(u="right"),z_(u,e,t,n)&&(u="center"),u}function rf(e,t,n){const r=n.yAlign||t.yAlign||T_(e,n);return{xAlign:n.xAlign||t.xAlign||D_(e,t,n,r),yAlign:r}}function R_(e,t){let{x:n,width:r}=e;return t==="right"?n-=r:t==="center"&&(n-=r/2),n}function L_(e,t,n){let{y:r,height:i}=e;return t==="top"?r+=n:t==="bottom"?r-=i+n:r-=i/2,r}function sf(e,t,n,r){const{caretSize:i,caretPadding:s,cornerRadius:a}=e,{xAlign:o,yAlign:l}=n,u=i+s,{topLeft:d,topRight:h,bottomLeft:f,bottomRight:p}=wr(a);let m=R_(t,o);const v=L_(t,l,u);return l==="center"?o==="left"?m+=u:o==="right"&&(m-=u):o==="left"?m-=Math.max(d,f)+i:o==="right"&&(m+=Math.max(h,p)+i),{x:Pe(m,0,r.width-t.width),y:Pe(v,0,r.height-t.height)}}function Hs(e,t,n){const r=ct(n.padding);return t==="center"?e.x+e.width/2:t==="right"?e.x+e.width-r.right:e.x+r.left}function af(e){return kt([],Tt(e))}function O_(e,t,n){return qn(e,{tooltip:t,tooltipItems:n,type:"tooltip"})}function of(e,t){const n=t&&t.dataset&&t.dataset.tooltip&&t.dataset.tooltip.callbacks;return n?e.override(n):e}const qg={beforeTitle:Mt,title(e){if(e.length>0){const t=e[0],n=t.chart.data.labels,r=n?n.length:0;if(this&&this.options&&this.options.mode==="dataset")return t.dataset.label||"";if(t.label)return t.label;if(r>0&&t.dataIndex<r)return n[t.dataIndex]}return""},afterTitle:Mt,beforeBody:Mt,beforeLabel:Mt,label(e){if(this&&this.options&&this.options.mode==="dataset")return e.label+": "+e.formattedValue||e.formattedValue;let t=e.dataset.label||"";t&&(t+=": ");const n=e.formattedValue;return Z(n)||(t+=n),t},labelColor(e){const n=e.chart.getDatasetMeta(e.datasetIndex).controller.getStyle(e.dataIndex);return{borderColor:n.borderColor,backgroundColor:n.backgroundColor,borderWidth:n.borderWidth,borderDash:n.borderDash,borderDashOffset:n.borderDashOffset,borderRadius:0}},labelTextColor(){return this.options.bodyColor},labelPointStyle(e){const n=e.chart.getDatasetMeta(e.datasetIndex).controller.getStyle(e.dataIndex);return{pointStyle:n.pointStyle,rotation:n.rotation}},afterLabel:Mt,afterBody:Mt,beforeFooter:Mt,footer:Mt,afterFooter:Mt};function Be(e,t,n,r){const i=e[t].call(n,r);return typeof i>"u"?qg[t].call(n,r):i}class fc extends vt{constructor(t){super(),this.opacity=0,this._active=[],this._eventPosition=void 0,this._size=void 0,this._cachedAnimations=void 0,this._tooltipItems=[],this.$animations=void 0,this.$context=void 0,this.chart=t.chart,this.options=t.options,this.dataPoints=void 0,this.title=void 0,this.beforeBody=void 0,this.body=void 0,this.afterBody=void 0,this.footer=void 0,this.xAlign=void 0,this.yAlign=void 0,this.x=void 0,this.y=void 0,this.height=void 0,this.width=void 0,this.caretX=void 0,this.caretY=void 0,this.labelColors=void 0,this.labelPointStyles=void 0,this.labelTextColors=void 0}initialize(t){this.options=t,this._cachedAnimations=void 0,this.$context=void 0}_resolveAnimations(){const t=this._cachedAnimations;if(t)return t;const n=this.chart,r=this.options.setContext(this.getContext()),i=r.enabled&&n.options.animation&&r.animations,s=new Dg(this.chart,i);return i._cacheable&&(this._cachedAnimations=Object.freeze(s)),s}getContext(){return this.$context||(this.$context=O_(this.chart.getContext(),this,this._tooltipItems))}getTitle(t,n){const{callbacks:r}=n,i=Be(r,"beforeTitle",this,t),s=Be(r,"title",this,t),a=Be(r,"afterTitle",this,t);let o=[];return o=kt(o,Tt(i)),o=kt(o,Tt(s)),o=kt(o,Tt(a)),o}getBeforeBody(t,n){return af(Be(n.callbacks,"beforeBody",this,t))}getBody(t,n){const{callbacks:r}=n,i=[];return Y(t,s=>{const a={before:[],lines:[],after:[]},o=of(r,s);kt(a.before,Tt(Be(o,"beforeLabel",this,s))),kt(a.lines,Be(o,"label",this,s)),kt(a.after,Tt(Be(o,"afterLabel",this,s))),i.push(a)}),i}getAfterBody(t,n){return af(Be(n.callbacks,"afterBody",this,t))}getFooter(t,n){const{callbacks:r}=n,i=Be(r,"beforeFooter",this,t),s=Be(r,"footer",this,t),a=Be(r,"afterFooter",this,t);let o=[];return o=kt(o,Tt(i)),o=kt(o,Tt(s)),o=kt(o,Tt(a)),o}_createItems(t){const n=this._active,r=this.chart.data,i=[],s=[],a=[];let o=[],l,u;for(l=0,u=n.length;l<u;++l)o.push(E_(this.chart,n[l]));return t.filter&&(o=o.filter((d,h,f)=>t.filter(d,h,f,r))),t.itemSort&&(o=o.sort((d,h)=>t.itemSort(d,h,r))),Y(o,d=>{const h=of(t.callbacks,d);i.push(Be(h,"labelColor",this,d)),s.push(Be(h,"labelPointStyle",this,d)),a.push(Be(h,"labelTextColor",this,d))}),this.labelColors=i,this.labelPointStyles=s,this.labelTextColors=a,this.dataPoints=o,o}update(t,n){const r=this.options.setContext(this.getContext()),i=this._active;let s,a=[];if(!i.length)this.opacity!==0&&(s={opacity:0});else{const o=di[r.position].call(this,i,this._eventPosition);a=this._createItems(r),this.title=this.getTitle(a,r),this.beforeBody=this.getBeforeBody(a,r),this.body=this.getBody(a,r),this.afterBody=this.getAfterBody(a,r),this.footer=this.getFooter(a,r);const l=this._size=nf(this,r),u=Object.assign({},o,l),d=rf(this.chart,r,u),h=sf(r,u,d,this.chart);this.xAlign=d.xAlign,this.yAlign=d.yAlign,s={opacity:1,x:h.x,y:h.y,width:l.width,height:l.height,caretX:o.x,caretY:o.y}}this._tooltipItems=a,this.$context=void 0,s&&this._resolveAnimations().update(this,s),t&&r.external&&r.external.call(this,{chart:this.chart,tooltip:this,replay:n})}drawCaret(t,n,r,i){const s=this.getCaretPosition(t,r,i);n.lineTo(s.x1,s.y1),n.lineTo(s.x2,s.y2),n.lineTo(s.x3,s.y3)}getCaretPosition(t,n,r){const{xAlign:i,yAlign:s}=this,{caretSize:a,cornerRadius:o}=r,{topLeft:l,topRight:u,bottomLeft:d,bottomRight:h}=wr(o),{x:f,y:p}=t,{width:m,height:v}=n;let y,g,x,b,k,w;return s==="center"?(k=p+v/2,i==="left"?(y=f,g=y-a,b=k+a,w=k-a):(y=f+m,g=y+a,b=k-a,w=k+a),x=y):(i==="left"?g=f+Math.max(l,d)+a:i==="right"?g=f+m-Math.max(u,h)-a:g=this.caretX,s==="top"?(b=p,k=b-a,y=g-a,x=g+a):(b=p+v,k=b+a,y=g+a,x=g-a),w=b),{x1:y,x2:g,x3:x,y1:b,y2:k,y3:w}}drawTitle(t,n,r){const i=this.title,s=i.length;let a,o,l;if(s){const u=_r(r.rtl,this.x,this.width);for(t.x=Hs(this,r.titleAlign,r),n.textAlign=u.textAlign(r.titleAlign),n.textBaseline="middle",a=Ee(r.titleFont),o=r.titleSpacing,n.fillStyle=r.titleColor,n.font=a.string,l=0;l<s;++l)n.fillText(i[l],u.x(t.x),t.y+a.lineHeight/2),t.y+=a.lineHeight+o,l+1===s&&(t.y+=r.titleMarginBottom-o)}}_drawColorBox(t,n,r,i,s){const a=this.labelColors[r],o=this.labelPointStyles[r],{boxHeight:l,boxWidth:u}=s,d=Ee(s.bodyFont),h=Hs(this,"left",s),f=i.x(h),p=l<d.lineHeight?(d.lineHeight-l)/2:0,m=n.y+p;if(s.usePointStyle){const v={radius:Math.min(u,l)/2,pointStyle:o.pointStyle,rotation:o.rotation,borderWidth:1},y=i.leftForLtr(f,u)+u/2,g=m+l/2;t.strokeStyle=s.multiKeyBackground,t.fillStyle=s.multiKeyBackground,lc(t,v,y,g),t.strokeStyle=a.borderColor,t.fillStyle=a.backgroundColor,lc(t,v,y,g)}else{t.lineWidth=$(a.borderWidth)?Math.max(...Object.values(a.borderWidth)):a.borderWidth||1,t.strokeStyle=a.borderColor,t.setLineDash(a.borderDash||[]),t.lineDashOffset=a.borderDashOffset||0;const v=i.leftForLtr(f,u),y=i.leftForLtr(i.xPlus(f,1),u-2),g=wr(a.borderRadius);Object.values(g).some(x=>x!==0)?(t.beginPath(),t.fillStyle=s.multiKeyBackground,Fa(t,{x:v,y:m,w:u,h:l,radius:g}),t.fill(),t.stroke(),t.fillStyle=a.backgroundColor,t.beginPath(),Fa(t,{x:y,y:m+1,w:u-2,h:l-2,radius:g}),t.fill()):(t.fillStyle=s.multiKeyBackground,t.fillRect(v,m,u,l),t.strokeRect(v,m,u,l),t.fillStyle=a.backgroundColor,t.fillRect(y,m+1,u-2,l-2))}t.fillStyle=this.labelTextColors[r]}drawBody(t,n,r){const{body:i}=this,{bodySpacing:s,bodyAlign:a,displayColors:o,boxHeight:l,boxWidth:u,boxPadding:d}=r,h=Ee(r.bodyFont);let f=h.lineHeight,p=0;const m=_r(r.rtl,this.x,this.width),v=function(N){n.fillText(N,m.x(t.x+p),t.y+f/2),t.y+=f+s},y=m.textAlign(a);let g,x,b,k,w,j,S;for(n.textAlign=a,n.textBaseline="middle",n.font=h.string,t.x=Hs(this,y,r),n.fillStyle=r.bodyColor,Y(this.beforeBody,v),p=o&&y!=="right"?a==="center"?u/2+d:u+2+d:0,k=0,j=i.length;k<j;++k){for(g=i[k],x=this.labelTextColors[k],n.fillStyle=x,Y(g.before,v),b=g.lines,o&&b.length&&(this._drawColorBox(n,t,k,m,r),f=Math.max(h.lineHeight,l)),w=0,S=b.length;w<S;++w)v(b[w]),f=h.lineHeight;Y(g.after,v)}p=0,f=h.lineHeight,Y(this.afterBody,v),t.y-=s}drawFooter(t,n,r){const i=this.footer,s=i.length;let a,o;if(s){const l=_r(r.rtl,this.x,this.width);for(t.x=Hs(this,r.footerAlign,r),t.y+=r.footerMarginTop,n.textAlign=l.textAlign(r.footerAlign),n.textBaseline="middle",a=Ee(r.footerFont),n.fillStyle=r.footerColor,n.font=a.string,o=0;o<s;++o)n.fillText(i[o],l.x(t.x),t.y+a.lineHeight/2),t.y+=a.lineHeight+r.footerSpacing}}drawBackground(t,n,r,i){const{xAlign:s,yAlign:a}=this,{x:o,y:l}=t,{width:u,height:d}=r,{topLeft:h,topRight:f,bottomLeft:p,bottomRight:m}=wr(i.cornerRadius);n.fillStyle=i.backgroundColor,n.strokeStyle=i.borderColor,n.lineWidth=i.borderWidth,n.beginPath(),n.moveTo(o+h,l),a==="top"&&this.drawCaret(t,n,r,i),n.lineTo(o+u-f,l),n.quadraticCurveTo(o+u,l,o+u,l+f),a==="center"&&s==="right"&&this.drawCaret(t,n,r,i),n.lineTo(o+u,l+d-m),n.quadraticCurveTo(o+u,l+d,o+u-m,l+d),a==="bottom"&&this.drawCaret(t,n,r,i),n.lineTo(o+p,l+d),n.quadraticCurveTo(o,l+d,o,l+d-p),a==="center"&&s==="left"&&this.drawCaret(t,n,r,i),n.lineTo(o,l+h),n.quadraticCurveTo(o,l,o+h,l),n.closePath(),n.fill(),i.borderWidth>0&&n.stroke()}_updateAnimationTarget(t){const n=this.chart,r=this.$animations,i=r&&r.x,s=r&&r.y;if(i||s){const a=di[t.position].call(this,this._active,this._eventPosition);if(!a)return;const o=this._size=nf(this,t),l=Object.assign({},a,this._size),u=rf(n,t,l),d=sf(t,l,u,n);(i._to!==d.x||s._to!==d.y)&&(this.xAlign=u.xAlign,this.yAlign=u.yAlign,this.width=o.width,this.height=o.height,this.caretX=a.x,this.caretY=a.y,this._resolveAnimations().update(this,d))}}_willRender(){return!!this.opacity}draw(t){const n=this.options.setContext(this.getContext());let r=this.opacity;if(!r)return;this._updateAnimationTarget(n);const i={width:this.width,height:this.height},s={x:this.x,y:this.y};r=Math.abs(r)<.001?0:r;const a=ct(n.padding),o=this.title.length||this.beforeBody.length||this.body.length||this.afterBody.length||this.footer.length;n.enabled&&o&&(t.save(),t.globalAlpha=r,this.drawBackground(s,t,i,n),Cg(t,n.textDirection),s.y+=a.top,this.drawTitle(s,t,n),this.drawBody(s,t,n),this.drawFooter(s,t,n),Mg(t,n.textDirection),t.restore())}getActiveElements(){return this._active||[]}setActiveElements(t,n){const r=this._active,i=t.map(({datasetIndex:o,index:l})=>{const u=this.chart.getDatasetMeta(o);if(!u)throw new Error("Cannot find a dataset at index "+o);return{datasetIndex:o,element:u.data[l],index:l}}),s=!Ra(r,i),a=this._positionChanged(i,n);(s||a)&&(this._active=i,this._eventPosition=n,this._ignoreReplayEvents=!0,this.update(!0))}handleEvent(t,n,r=!0){if(n&&this._ignoreReplayEvents)return!1;this._ignoreReplayEvents=!1;const i=this.options,s=this._active||[],a=this._getActiveElements(t,s,n,r),o=this._positionChanged(a,t),l=n||!Ra(a,s)||o;return l&&(this._active=a,(i.enabled||i.external)&&(this._eventPosition={x:t.x,y:t.y},this.update(!0,n))),l}_getActiveElements(t,n,r,i){const s=this.options;if(t.type==="mouseout")return[];if(!i)return n.filter(o=>this.chart.data.datasets[o.datasetIndex]&&this.chart.getDatasetMeta(o.datasetIndex).controller.getParsed(o.index)!==void 0);const a=this.chart.getElementsAtEventForMode(t,s.mode,s,r);return s.reverse&&a.reverse(),a}_positionChanged(t,n){const{caretX:r,caretY:i,options:s}=this,a=di[s.position].call(this,t,n);return a!==!1&&(r!==a.x||i!==a.y)}}R(fc,"positioners",di);var Du={id:"tooltip",_element:fc,positioners:di,afterInit(e,t,n){n&&(e.tooltip=new fc({chart:e,options:n}))},beforeUpdate(e,t,n){e.tooltip&&e.tooltip.initialize(n)},reset(e,t,n){e.tooltip&&e.tooltip.initialize(n)},afterDraw(e){const t=e.tooltip;if(t&&t._willRender()){const n={tooltip:t};if(e.notifyPlugins("beforeTooltipDraw",{...n,cancelable:!0})===!1)return;t.draw(e.ctx),e.notifyPlugins("afterTooltipDraw",n)}},afterEvent(e,t){if(e.tooltip){const n=t.replay;e.tooltip.handleEvent(t.event,n,t.inChartArea)&&(t.changed=!0)}},defaults:{enabled:!0,external:null,position:"average",backgroundColor:"rgba(0,0,0,0.8)",titleColor:"#fff",titleFont:{weight:"bold"},titleSpacing:2,titleMarginBottom:6,titleAlign:"left",bodyColor:"#fff",bodySpacing:2,bodyFont:{},bodyAlign:"left",footerColor:"#fff",footerSpacing:2,footerMarginTop:6,footerFont:{weight:"bold"},footerAlign:"left",padding:6,caretPadding:2,caretSize:5,cornerRadius:6,boxHeight:(e,t)=>t.bodyFont.size,boxWidth:(e,t)=>t.bodyFont.size,multiKeyBackground:"#fff",displayColors:!0,boxPadding:0,borderColor:"rgba(0,0,0,0)",borderWidth:0,animation:{duration:400,easing:"easeOutQuart"},animations:{numbers:{type:"number",properties:["x","y","width","height","caretX","caretY"]},opacity:{easing:"linear",duration:200}},callbacks:qg},defaultRoutes:{bodyFont:"font",footerFont:"font",titleFont:"font"},descriptors:{_scriptable:e=>e!=="filter"&&e!=="itemSort"&&e!=="external",_indexable:!1,callbacks:{_scriptable:!1,_indexable:!1},animation:{_fallback:!1},animations:{_fallback:"animation"}},additionalOptionScopes:["interaction"]};const A_=(e,t,n,r)=>(typeof t=="string"?(n=e.push(t)-1,r.unshift({index:n,label:t})):isNaN(t)&&(n=null),n);function I_(e,t,n,r){const i=e.indexOf(t);if(i===-1)return A_(e,t,n,r);const s=e.lastIndexOf(t);return i!==s?n:i}const F_=(e,t)=>e===null?null:Pe(Math.round(e),0,t);function lf(e){const t=this.getLabels();return e>=0&&e<t.length?t[e]:e}class Wa extends Hr{constructor(t){super(t),this._startValue=void 0,this._valueRange=0,this._addedLabels=[]}init(t){const n=this._addedLabels;if(n.length){const r=this.getLabels();for(const{index:i,label:s}of n)r[i]===s&&r.splice(i,1);this._addedLabels=[]}super.init(t)}parse(t,n){if(Z(t))return null;const r=this.getLabels();return n=isFinite(n)&&r[n]===t?n:I_(r,t,B(n,t),this._addedLabels),F_(n,r.length-1)}determineDataLimits(){const{minDefined:t,maxDefined:n}=this.getUserBounds();let{min:r,max:i}=this.getMinMax(!0);this.options.bounds==="ticks"&&(t||(r=0),n||(i=this.getLabels().length-1)),this.min=r,this.max=i}buildTicks(){const t=this.min,n=this.max,r=this.options.offset,i=[];let s=this.getLabels();s=t===0&&n===s.length-1?s:s.slice(t,n+1),this._valueRange=Math.max(s.length-(r?0:1),1),this._startValue=this.min-(r?.5:0);for(let a=t;a<=n;a++)i.push({value:a});return i}getLabelForValue(t){return lf.call(this,t)}configure(){super.configure(),this.isHorizontal()||(this._reversePixels=!this._reversePixels)}getPixelForValue(t){return typeof t!="number"&&(t=this.parse(t)),t===null?NaN:this.getPixelForDecimal((t-this._startValue)/this._valueRange)}getPixelForTick(t){const n=this.ticks;return t<0||t>n.length-1?null:this.getPixelForValue(n[t].value)}getValueForPixel(t){return Math.round(this._startValue+this.getDecimalForPixel(t)*this._valueRange)}getBasePixel(){return this.bottom}}R(Wa,"id","category"),R(Wa,"defaults",{ticks:{callback:lf}});function B_(e,t){const n=[],{bounds:i,step:s,min:a,max:o,precision:l,count:u,maxTicks:d,maxDigits:h,includeBounds:f}=e,p=s||1,m=d-1,{min:v,max:y}=t,g=!Z(a),x=!Z(o),b=!Z(u),k=(y-v)/(h+1);let w=oh((y-v)/m/p)*p,j,S,N,T;if(w<1e-14&&!g&&!x)return[{value:v},{value:y}];T=Math.ceil(y/w)-Math.floor(v/w),T>m&&(w=oh(T*w/m/p)*p),Z(l)||(j=Math.pow(10,l),w=Math.ceil(w*j)/j),i==="ticks"?(S=Math.floor(v/w)*w,N=Math.ceil(y/w)*w):(S=v,N=y),g&&x&&s&&nb((o-a)/s,w/1e3)?(T=Math.round(Math.min((o-a)/w,d)),w=(o-a)/T,S=a,N=o):b?(S=g?a:S,N=x?o:N,T=u-1,w=(N-S)/T):(T=(N-S)/w,wi(T,Math.round(T),w/1e3)?T=Math.round(T):T=Math.ceil(T));const E=Math.max(lh(w),lh(S));j=Math.pow(10,Z(l)?E:l),S=Math.round(S*j)/j,N=Math.round(N*j)/j;let L=0;for(g&&(f&&S!==a?(n.push({value:a}),S<a&&L++,wi(Math.round((S+L*w)*j)/j,a,cf(a,k,e))&&L++):S<a&&L++);L<T;++L){const A=Math.round((S+L*w)*j)/j;if(x&&A>o)break;n.push({value:A})}return x&&f&&N!==o?n.length&&wi(n[n.length-1].value,o,cf(o,k,e))?n[n.length-1].value=o:n.push({value:o}):(!x||N===o)&&n.push({value:N}),n}function cf(e,t,{horizontal:n,minRotation:r}){const i=Dn(r),s=(n?Math.sin(i):Math.cos(i))||.001,a=.75*t*(""+e).length;return Math.min(t/s,a)}class $_ extends Hr{constructor(t){super(t),this.start=void 0,this.end=void 0,this._startValue=void 0,this._endValue=void 0,this._valueRange=0}parse(t,n){return Z(t)||(typeof t=="number"||t instanceof Number)&&!isFinite(+t)?null:+t}handleTickRangeOptions(){const{beginAtZero:t}=this.options,{minDefined:n,maxDefined:r}=this.getUserBounds();let{min:i,max:s}=this;const a=l=>i=n?i:l,o=l=>s=r?s:l;if(t){const l=zr(i),u=zr(s);l<0&&u<0?o(0):l>0&&u>0&&a(0)}if(i===s){let l=s===0?1:Math.abs(s*.05);o(s+l),t||a(i-l)}this.min=i,this.max=s}getTickLimit(){const t=this.options.ticks;let{maxTicksLimit:n,stepSize:r}=t,i;return r?(i=Math.ceil(this.max/r)-Math.floor(this.min/r)+1,i>1e3&&(console.warn(`scales.${this.id}.ticks.stepSize: ${r} would result generating up to ${i} ticks. Limiting to 1000.`),i=1e3)):(i=this.computeTickLimit(),n=n||11),n&&(i=Math.min(n,i)),i}computeTickLimit(){return Number.POSITIVE_INFINITY}buildTicks(){const t=this.options,n=t.ticks;let r=this.getTickLimit();r=Math.max(2,r);const i={maxTicks:r,bounds:t.bounds,min:t.min,max:t.max,precision:n.precision,step:n.stepSize,count:n.count,maxDigits:this._maxDigits(),horizontal:this.isHorizontal(),minRotation:n.minRotation||0,includeBounds:n.includeBounds!==!1},s=this._range||this,a=B_(i,s);return t.bounds==="ticks"&&rb(a,this,"value"),t.reverse?(a.reverse(),this.start=this.max,this.end=this.min):(this.start=this.min,this.end=this.max),a}configure(){const t=this.ticks;let n=this.min,r=this.max;if(super.configure(),this.options.offset&&t.length){const i=(r-n)/Math.max(t.length-1,1)/2;n-=i,r+=i}this._startValue=n,this._endValue=r,this._valueRange=r-n}getLabelForValue(t){return yg(t,this.chart.options.locale,this.options.ticks.format)}}class Va extends $_{determineDataLimits(){const{min:t,max:n}=this.getMinMax(!0);this.min=De(t)?t:0,this.max=De(n)?n:1,this.handleTickRangeOptions()}computeTickLimit(){const t=this.isHorizontal(),n=t?this.width:this.height,r=Dn(this.options.ticks.minRotation),i=(t?Math.sin(r):Math.cos(r))||.001,s=this._resolveTickFontOptions(0);return Math.ceil(n/Math.min(40,s.lineHeight/i))}getPixelForValue(t){return t===null?NaN:this.getPixelForDecimal((t-this._startValue)/this._valueRange)}getValueForPixel(t){return this._startValue+this.getDecimalForPixel(t)*this._valueRange}}R(Va,"id","linear"),R(Va,"defaults",{ticks:{callback:xg.formatters.numeric}});const go={millisecond:{common:!0,size:1,steps:1e3},second:{common:!0,size:1e3,steps:60},minute:{common:!0,size:6e4,steps:60},hour:{common:!0,size:36e5,steps:24},day:{common:!0,size:864e5,steps:30},week:{common:!1,size:6048e5,steps:4},month:{common:!0,size:2628e6,steps:12},quarter:{common:!1,size:7884e6,steps:4},year:{common:!0,size:3154e7}},He=Object.keys(go);function uf(e,t){return e-t}function df(e,t){if(Z(t))return null;const n=e._adapter,{parser:r,round:i,isoWeekday:s}=e._parseOpts;let a=t;return typeof r=="function"&&(a=r(a)),De(a)||(a=typeof r=="string"?n.parse(a,r):n.parse(a)),a===null?null:(i&&(a=i==="week"&&(Gi(s)||s===!0)?n.startOf(a,"isoWeek",s):n.startOf(a,i)),+a)}function hf(e,t,n,r){const i=He.length;for(let s=He.indexOf(e);s<i-1;++s){const a=go[He[s]],o=a.steps?a.steps:Number.MAX_SAFE_INTEGER;if(a.common&&Math.ceil((n-t)/(o*a.size))<=r)return He[s]}return He[i-1]}function H_(e,t,n,r,i){for(let s=He.length-1;s>=He.indexOf(n);s--){const a=He[s];if(go[a].common&&e._adapter.diff(i,r,a)>=t-1)return a}return He[n?He.indexOf(n):0]}function W_(e){for(let t=He.indexOf(e)+1,n=He.length;t<n;++t)if(go[He[t]].common)return He[t]}function ff(e,t,n){if(!n)e[t]=!0;else if(n.length){const{lo:r,hi:i}=wu(n,t),s=n[r]>=t?n[r]:n[i];e[s]=!0}}function V_(e,t,n,r){const i=e._adapter,s=+i.startOf(t[0].value,r),a=t[t.length-1].value;let o,l;for(o=s;o<=a;o=+i.add(o,1,r))l=n[o],l>=0&&(t[l].major=!0);return t}function pf(e,t,n){const r=[],i={},s=t.length;let a,o;for(a=0;a<s;++a)o=t[a],i[o]=a,r.push({value:o,major:!1});return s===0||!n?r:V_(e,r,i,n)}class Ua extends Hr{constructor(t){super(t),this._cache={data:[],labels:[],all:[]},this._unit="day",this._majorUnit=void 0,this._offsets={},this._normalized=!1,this._parseOpts=void 0}init(t,n={}){const r=t.time||(t.time={}),i=this._adapter=new Pk._date(t.adapters.date);i.init(n),ki(r.displayFormats,i.formats()),this._parseOpts={parser:r.parser,round:r.round,isoWeekday:r.isoWeekday},super.init(t),this._normalized=n.normalized}parse(t,n){return t===void 0?null:df(this,t)}beforeLayout(){super.beforeLayout(),this._cache={data:[],labels:[],all:[]}}determineDataLimits(){const t=this.options,n=this._adapter,r=t.time.unit||"day";let{min:i,max:s,minDefined:a,maxDefined:o}=this.getUserBounds();function l(u){!a&&!isNaN(u.min)&&(i=Math.min(i,u.min)),!o&&!isNaN(u.max)&&(s=Math.max(s,u.max))}(!a||!o)&&(l(this._getLabelBounds()),(t.bounds!=="ticks"||t.ticks.source!=="labels")&&l(this.getMinMax(!1))),i=De(i)&&!isNaN(i)?i:+n.startOf(Date.now(),r),s=De(s)&&!isNaN(s)?s:+n.endOf(Date.now(),r)+1,this.min=Math.min(i,s-1),this.max=Math.max(i+1,s)}_getLabelBounds(){const t=this.getLabelTimestamps();let n=Number.POSITIVE_INFINITY,r=Number.NEGATIVE_INFINITY;return t.length&&(n=t[0],r=t[t.length-1]),{min:n,max:r}}buildTicks(){const t=this.options,n=t.time,r=t.ticks,i=r.source==="labels"?this.getLabelTimestamps():this._generate();t.bounds==="ticks"&&i.length&&(this.min=this._userMin||i[0],this.max=this._userMax||i[i.length-1]);const s=this.min,a=this.max,o=lb(i,s,a);return this._unit=n.unit||(r.autoSkip?hf(n.minUnit,this.min,this.max,this._getLabelCapacity(s)):H_(this,o.length,n.minUnit,this.min,this.max)),this._majorUnit=!r.major.enabled||this._unit==="year"?void 0:W_(this._unit),this.initOffsets(i),t.reverse&&o.reverse(),pf(this,o,this._majorUnit)}afterAutoSkip(){this.options.offsetAfterAutoskip&&this.initOffsets(this.ticks.map(t=>+t.value))}initOffsets(t=[]){let n=0,r=0,i,s;this.options.offset&&t.length&&(i=this.getDecimalForValue(t[0]),t.length===1?n=1-i:n=(this.getDecimalForValue(t[1])-i)/2,s=this.getDecimalForValue(t[t.length-1]),t.length===1?r=s:r=(s-this.getDecimalForValue(t[t.length-2]))/2);const a=t.length<3?.5:.25;n=Pe(n,0,a),r=Pe(r,0,a),this._offsets={start:n,end:r,factor:1/(n+1+r)}}_generate(){const t=this._adapter,n=this.min,r=this.max,i=this.options,s=i.time,a=s.unit||hf(s.minUnit,n,r,this._getLabelCapacity(n)),o=B(i.ticks.stepSize,1),l=a==="week"?s.isoWeekday:!1,u=Gi(l)||l===!0,d={};let h=n,f,p;if(u&&(h=+t.startOf(h,"isoWeek",l)),h=+t.startOf(h,u?"day":a),t.diff(r,n,a)>1e5*o)throw new Error(n+" and "+r+" are too far apart with stepSize of "+o+" "+a);const m=i.ticks.source==="data"&&this.getDataTimestamps();for(f=h,p=0;f<r;f=+t.add(f,o,a),p++)ff(d,f,m);return(f===r||i.bounds==="ticks"||p===1)&&ff(d,f,m),Object.keys(d).sort(uf).map(v=>+v)}getLabelForValue(t){const n=this._adapter,r=this.options.time;return r.tooltipFormat?n.format(t,r.tooltipFormat):n.format(t,r.displayFormats.datetime)}format(t,n){const i=this.options.time.displayFormats,s=this._unit,a=n||i[s];return this._adapter.format(t,a)}_tickFormatFunction(t,n,r,i){const s=this.options,a=s.ticks.callback;if(a)return te(a,[t,n,r],this);const o=s.time.displayFormats,l=this._unit,u=this._majorUnit,d=l&&o[l],h=u&&o[u],f=r[n],p=u&&h&&f&&f.major;return this._adapter.format(t,i||(p?h:d))}generateTickLabels(t){let n,r,i;for(n=0,r=t.length;n<r;++n)i=t[n],i.label=this._tickFormatFunction(i.value,n,t)}getDecimalForValue(t){return t===null?NaN:(t-this.min)/(this.max-this.min)}getPixelForValue(t){const n=this._offsets,r=this.getDecimalForValue(t);return this.getPixelForDecimal((n.start+r)*n.factor)}getValueForPixel(t){const n=this._offsets,r=this.getDecimalForPixel(t)/n.factor-n.end;return this.min+r*(this.max-this.min)}_getLabelSize(t){const n=this.options.ticks,r=this.ctx.measureText(t).width,i=Dn(this.isHorizontal()?n.maxRotation:n.minRotation),s=Math.cos(i),a=Math.sin(i),o=this._resolveTickFontOptions(0).size;return{w:r*s+o*a,h:r*a+o*s}}_getLabelCapacity(t){const n=this.options.time,r=n.displayFormats,i=r[n.unit]||r.millisecond,s=this._tickFormatFunction(t,0,pf(this,[t],this._majorUnit),i),a=this._getLabelSize(s),o=Math.floor(this.isHorizontal()?this.width/a.w:this.height/a.h)-1;return o>0?o:1}getDataTimestamps(){let t=this._cache.data||[],n,r;if(t.length)return t;const i=this.getMatchingVisibleMetas();if(this._normalized&&i.length)return this._cache.data=i[0].controller.getAllParsedValues(this);for(n=0,r=i.length;n<r;++n)t=t.concat(i[n].controller.getAllParsedValues(this));return this._cache.data=this.normalize(t)}getLabelTimestamps(){const t=this._cache.labels||[];let n,r;if(t.length)return t;const i=this.getLabels();for(n=0,r=i.length;n<r;++n)t.push(df(this,i[n]));return this._cache.labels=this._normalized?t:this.normalize(t)}normalize(t){return ub(t.sort(uf))}}R(Ua,"id","time"),R(Ua,"defaults",{bounds:"data",adapters:{},time:{parser:!1,unit:!1,round:!1,isoWeekday:!1,minUnit:"millisecond",displayFormats:{}},ticks:{source:"auto",callback:!1,major:{enabled:!1}}});function Ws(e,t,n){let r=0,i=e.length-1,s,a,o,l;n?(t>=e[r].pos&&t<=e[i].pos&&({lo:r,hi:i}=Rn(e,"pos",t)),{pos:s,time:o}=e[r],{pos:a,time:l}=e[i]):(t>=e[r].time&&t<=e[i].time&&({lo:r,hi:i}=Rn(e,"time",t)),{time:s,pos:o}=e[r],{time:a,pos:l}=e[i]);const u=a-s;return u?o+(l-o)*(t-s)/u:o}class mf extends Ua{constructor(t){super(t),this._table=[],this._minPos=void 0,this._tableRange=void 0}initOffsets(){const t=this._getTimestampsForTable(),n=this._table=this.buildLookupTable(t);this._minPos=Ws(n,this.min),this._tableRange=Ws(n,this.max)-this._minPos,super.initOffsets(t)}buildLookupTable(t){const{min:n,max:r}=this,i=[],s=[];let a,o,l,u,d;for(a=0,o=t.length;a<o;++a)u=t[a],u>=n&&u<=r&&i.push(u);if(i.length<2)return[{time:n,pos:0},{time:r,pos:1}];for(a=0,o=i.length;a<o;++a)d=i[a+1],l=i[a-1],u=i[a],Math.round((d+l)/2)!==u&&s.push({time:u,pos:a/(o-1)});return s}_generate(){const t=this.min,n=this.max;let r=super.getDataTimestamps();return(!r.includes(t)||!r.length)&&r.splice(0,0,t),(!r.includes(n)||r.length===1)&&r.push(n),r.sort((i,s)=>i-s)}_getTimestampsForTable(){let t=this._cache.all||[];if(t.length)return t;const n=this.getDataTimestamps(),r=this.getLabelTimestamps();return n.length&&r.length?t=this.normalize(n.concat(r)):t=n.length?n:r,t=this._cache.all=t,t}getDecimalForValue(t){return(Ws(this._table,t)-this._minPos)/this._tableRange}getValueForPixel(t){const n=this._offsets,r=this.getDecimalForPixel(t)/n.factor-n.end;return Ws(this._table,r*this._tableRange+this._minPos,!0)}}R(mf,"id","timeseries"),R(mf,"defaults",Ua.defaults);const Jg="label";function gf(e,t){typeof e=="function"?e(t):e&&(e.current=t)}function U_(e,t){const n=e.options;n&&t&&Object.assign(n,t)}function ev(e,t){e.labels=t}function tv(e,t,n=Jg){const r=[];e.datasets=t.map(i=>{const s=e.datasets.find(a=>a[n]===i[n]);return!s||!i.data||r.includes(s)?{...i}:(r.push(s),Object.assign(s,i),s)})}function Y_(e,t=Jg){const n={labels:[],datasets:[]};return ev(n,e.labels),tv(n,e.datasets,t),n}function X_(e,t){const{height:n=150,width:r=300,redraw:i=!1,datasetIdKey:s,type:a,data:o,options:l,plugins:u=[],fallbackContent:d,updateMode:h,...f}=e,p=_.useRef(null),m=_.useRef(null),v=()=>{p.current&&(m.current=new Wr(p.current,{type:a,data:Y_(o,s),options:l&&{...l},plugins:u}),gf(t,m.current))},y=()=>{gf(t,null),m.current&&(m.current.destroy(),m.current=null)};return _.useEffect(()=>{!i&&m.current&&l&&U_(m.current,l)},[i,l]),_.useEffect(()=>{!i&&m.current&&ev(m.current.config.data,o.labels)},[i,o.labels]),_.useEffect(()=>{!i&&m.current&&o.datasets&&tv(m.current.config.data,o.datasets,s)},[i,o.datasets]),_.useEffect(()=>{m.current&&(i?(y(),setTimeout(v)):m.current.update(h))},[i,l,o.labels,o.datasets,h]),_.useEffect(()=>{m.current&&(y(),setTimeout(v))},[a]),_.useEffect(()=>(v(),()=>y()),[]),c.jsx("canvas",{ref:p,role:"img",height:n,width:r,...f,children:d})}const K_=_.forwardRef(X_);function Q_(e,t){return Wr.register(t),_.forwardRef((n,r)=>c.jsx(K_,{...n,ref:r,type:e}))}const G_=Q_("line",ra);Wr.register(Wa,Va,aa,nn,Zg,Du,zu,__);const nv=({data:e,title:t="Score Over Time",height:n=300,showLegend:r=!1,fill:i=!0,color:s="#00ff88",secondaryData:a,secondaryLabel:o="Secondary",secondaryColor:l="#00d4ff"})=>{var p;const u=e.map(m=>new Date(m.timestamp).toLocaleDateString(void 0,{month:"short",day:"numeric"})),d=[{label:((p=e[0])==null?void 0:p.label)||"Score",data:e.map(m=>m.score),borderColor:s,backgroundColor:i?`${s}20`:"transparent",fill:i,tension:.4,pointRadius:4,pointHoverRadius:6,pointBackgroundColor:s,pointBorderColor:"var(--bg-secondary)",pointBorderWidth:2}];a&&a.length>0&&d.push({label:o,data:a.map(m=>m.score),borderColor:l,backgroundColor:"transparent",fill:!1,tension:.4,pointRadius:3,pointHoverRadius:5,pointBackgroundColor:l,pointBorderColor:"var(--bg-secondary)",pointBorderWidth:2});const h={labels:u,datasets:d},f={responsive:!0,maintainAspectRatio:!1,plugins:{legend:{display:r,position:"top",labels:{color:"#a0aec0",font:{family:"JetBrains Mono, monospace",size:11},padding:16,usePointStyle:!0}},title:{display:!!t,text:t,color:"#e2e8f0",font:{family:"Inter, sans-serif",size:14,weight:"600"},padding:{bottom:16}},tooltip:{backgroundColor:"#1a1a24",borderColor:"#2d2d3a",borderWidth:1,titleColor:"#e2e8f0",bodyColor:"#a0aec0",titleFont:{family:"Inter, sans-serif",size:12,weight:"600"},bodyFont:{family:"JetBrains Mono, monospace",size:12},padding:12,cornerRadius:8,displayColors:!0,callbacks:{label:m=>`${m.dataset.label}: ${m.parsed.y.toFixed(3)}`}}},scales:{x:{grid:{color:"#2d2d3a",lineWidth:1},ticks:{color:"#718096",font:{family:"JetBrains Mono, monospace",size:10}},border:{color:"#2d2d3a"}},y:{min:0,max:1,grid:{color:"#2d2d3a",lineWidth:1},ticks:{color:"#718096",font:{family:"JetBrains Mono, monospace",size:10},callback:m=>typeof m=="number"?m.toFixed(2):m},border:{color:"#2d2d3a"}}},interaction:{intersect:!1,mode:"index"}};return c.jsxs("div",{className:"score-line-chart",style:{height:n},children:[c.jsx(G_,{data:h,options:f}),c.jsx("style",{children:`
        .score-line-chart {
          width: 100%;
          padding: var(--space-4);
          background: var(--bg-secondary);
          border: 1px solid var(--border-primary);
          border-radius: var(--radius-lg);
        }
      `})]})};Wr.register(ui,Du,zu);Wr.register(Wa,Va,oa,Zg,Du,zu);const Te=({title:e,value:t,icon:n,trend:r,trendLabel:i,subtitle:s,variant:a="default",size:o="md",loading:l=!1})=>{const u=()=>r===void 0||r===0?c.jsx(Ui,{className:"trend-icon"}):r>0?c.jsx(Xn,{className:"trend-icon trend-up"}):c.jsx(Br,{className:"trend-icon trend-down"}),d=()=>r===void 0||r===0?"":r>0?"trend-positive":"trend-negative";return l?c.jsxs("div",{className:`stats-card size-${o} variant-${a} loading`,children:[c.jsx("div",{className:"skeleton skeleton-text",style:{width:"40%",height:"12px"}}),c.jsx("div",{className:"skeleton skeleton-text",style:{width:"60%",height:"28px",marginTop:"8px"}}),c.jsx("div",{className:"skeleton skeleton-text",style:{width:"30%",height:"12px",marginTop:"8px"}}),c.jsx("style",{children:vf})]}):c.jsxs("div",{className:`stats-card size-${o} variant-${a}`,children:[c.jsxs("div",{className:"stats-header",children:[c.jsx("span",{className:"stats-title",children:e}),n&&c.jsx("div",{className:"stats-icon",children:c.jsx(n,{})})]}),c.jsx("div",{className:"stats-value",children:t}),c.jsxs("div",{className:"stats-footer",children:[r!==void 0&&c.jsxs("span",{className:`stats-trend ${d()}`,children:[u(),c.jsxs("span",{children:[Math.abs(r),"%"]}),i&&c.jsx("span",{className:"trend-label",children:i})]}),s&&c.jsx("span",{className:"stats-subtitle",children:s})]}),c.jsx("style",{children:vf})]})},vf=`
  .stats-card {
    padding: var(--space-4);
    background: var(--bg-secondary);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-lg);
    transition: all var(--transition-fast);
  }

  .stats-card:hover {
    border-color: var(--border-secondary);
  }

  .stats-card.size-sm {
    padding: var(--space-3);
  }

  .stats-card.size-lg {
    padding: var(--space-5);
  }

  .stats-card.variant-primary {
    border-left: 3px solid var(--accent-primary);
  }

  .stats-card.variant-success {
    border-left: 3px solid var(--accent-primary);
  }

  .stats-card.variant-warning {
    border-left: 3px solid var(--accent-warning);
  }

  .stats-card.variant-danger {
    border-left: 3px solid var(--accent-danger);
  }

  .stats-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: var(--space-2);
  }

  .stats-title {
    font-size: var(--text-xs);
    font-weight: var(--weight-medium);
    color: var(--text-tertiary);
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .stats-icon {
    width: 32px;
    height: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--bg-tertiary);
    border-radius: var(--radius-md);
    color: var(--text-secondary);
  }

  .variant-primary .stats-icon {
    background: var(--accent-primary-dim);
    color: var(--accent-primary);
  }

  .variant-success .stats-icon {
    background: var(--accent-primary-dim);
    color: var(--accent-primary);
  }

  .variant-warning .stats-icon {
    background: var(--accent-warning-dim);
    color: var(--accent-warning);
  }

  .variant-danger .stats-icon {
    background: var(--accent-danger-dim);
    color: var(--accent-danger);
  }

  .stats-value {
    font-family: var(--font-mono);
    font-weight: var(--weight-bold);
    color: var(--text-primary);
  }

  .size-sm .stats-value {
    font-size: var(--text-xl);
  }

  .size-md .stats-value {
    font-size: var(--text-2xl);
  }

  .size-lg .stats-value {
    font-size: var(--text-3xl);
  }

  .stats-footer {
    display: flex;
    align-items: center;
    gap: var(--space-2);
    margin-top: var(--space-2);
    font-size: var(--text-xs);
  }

  .stats-trend {
    display: flex;
    align-items: center;
    gap: var(--space-1);
    color: var(--text-tertiary);
  }

  .stats-trend.trend-positive {
    color: var(--accent-primary);
  }

  .stats-trend.trend-negative {
    color: var(--accent-danger);
  }

  .trend-icon {
    width: 14px;
    height: 14px;
  }

  .trend-label {
    color: var(--text-tertiary);
    margin-left: var(--space-1);
  }

  .stats-subtitle {
    color: var(--text-tertiary);
  }

  .stats-card.loading {
    display: flex;
    flex-direction: column;
    gap: var(--space-2);
  }
`,vo=({children:e,columns:t=4})=>c.jsxs("div",{className:`stats-grid cols-${t}`,children:[e,c.jsx("style",{children:`
        .stats-grid {
          display: grid;
          gap: var(--space-4);
        }

        .stats-grid.cols-2 {
          grid-template-columns: repeat(2, 1fr);
        }

        .stats-grid.cols-3 {
          grid-template-columns: repeat(3, 1fr);
        }

        .stats-grid.cols-4 {
          grid-template-columns: repeat(4, 1fr);
        }

        @media (max-width: 1024px) {
          .stats-grid.cols-4 {
            grid-template-columns: repeat(2, 1fr);
          }
        }

        @media (max-width: 640px) {
          .stats-grid {
            grid-template-columns: 1fr;
          }
        }
      `})]}),Z_=({isOpen:e,onClose:t,task:n,onFeedback:r,onRetry:i})=>{if(!n)return null;const s=d=>{switch(d){case"completed":return c.jsx(hu,{className:"icon status-completed"});case"failed":return c.jsx(pu,{className:"icon status-failed"});case"running":return c.jsx(gn,{className:"icon status-running"});case"pending":return c.jsx(Xm,{className:"icon status-pending"});default:return null}},a=d=>d===void 0?"var(--text-tertiary)":d>=.85?"var(--accent-primary)":d>=.7?"var(--accent-secondary)":d>=.5?"var(--accent-warning)":"var(--accent-danger)",o=d=>{if(!d)return"-";if(d<60)return`${d.toFixed(1)}s`;const h=Math.floor(d/60),f=d%60;return`${h}m ${f.toFixed(0)}s`},l=d=>new Date(d).toLocaleString(),u="input"in n;return c.jsxs($r,{isOpen:e,onClose:t,title:"Task Details",size:"lg",children:[c.jsxs("div",{className:"task-detail",children:[c.jsxs("div",{className:"task-detail-header",children:[c.jsx("div",{className:"task-status-icon",children:s(n.status)}),c.jsxs("div",{className:"task-header-info",children:[c.jsx("h3",{className:"task-title",children:n.task_name}),c.jsxs("div",{className:"task-id",children:["#",n.id]})]}),c.jsx(gu,{status:n.status})]}),c.jsxs("div",{className:"task-meta-grid",children:[c.jsxs("div",{className:"meta-item",children:[c.jsx(h1,{className:"icon-sm"}),c.jsxs("div",{children:[c.jsx("div",{className:"meta-label",children:"Specialist"}),c.jsx("div",{className:"meta-value",children:n.specialist_name||"-"})]})]}),c.jsxs("div",{className:"meta-item",children:[c.jsx(os,{className:"icon-sm"}),c.jsxs("div",{children:[c.jsx("div",{className:"meta-label",children:"Timestamp"}),c.jsx("div",{className:"meta-value",children:l(n.timestamp)})]})]}),c.jsxs("div",{className:"meta-item",children:[c.jsx(d1,{className:"icon-sm"}),c.jsxs("div",{children:[c.jsx("div",{className:"meta-label",children:"Duration"}),c.jsx("div",{className:"meta-value",children:o(n.duration)})]})]}),c.jsxs("div",{className:"meta-item",children:[c.jsx(Zm,{className:"icon-sm"}),c.jsxs("div",{children:[c.jsx("div",{className:"meta-label",children:"Score"}),c.jsx("div",{className:"meta-value score",style:{color:a(n.score)},children:n.score!==void 0?n.score.toFixed(3):"-"})]})]})]}),u&&c.jsxs(c.Fragment,{children:[n.input&&c.jsxs("div",{className:"task-section",children:[c.jsx("h4",{className:"section-title",children:"Input"}),c.jsx("pre",{className:"task-code",children:n.input})]}),n.output&&c.jsxs("div",{className:"task-section",children:[c.jsx("h4",{className:"section-title",children:"Output"}),c.jsx("pre",{className:"task-code",children:n.output})]}),n.error&&c.jsxs("div",{className:"task-section error",children:[c.jsx("h4",{className:"section-title",children:"Error"}),c.jsx("pre",{className:"task-code error",children:n.error})]})]}),n.status==="completed"&&r&&c.jsxs("div",{className:"task-feedback",children:[c.jsx("h4",{className:"section-title",children:"Provide Feedback"}),c.jsx(k1,{taskId:n.id,specialistId:n.specialist_id,onFeedback:d=>r({taskId:d.taskId,type:d.type,comment:d.comment})})]}),n.status==="failed"&&i&&c.jsx("div",{className:"task-actions",children:c.jsx("button",{className:"retry-button",onClick:i,children:"Retry Task"})})]}),c.jsx("style",{children:`
        .task-detail {
          display: flex;
          flex-direction: column;
          gap: var(--space-4);
        }

        .task-detail-header {
          display: flex;
          align-items: center;
          gap: var(--space-3);
          padding-bottom: var(--space-4);
          border-bottom: 1px solid var(--border-primary);
        }

        .task-status-icon {
          width: 48px;
          height: 48px;
          display: flex;
          align-items: center;
          justify-content: center;
          background: var(--bg-tertiary);
          border-radius: var(--radius-md);
        }

        .status-completed {
          color: var(--accent-primary);
        }

        .status-failed {
          color: var(--accent-danger);
        }

        .status-running {
          color: var(--accent-secondary);
          animation: spin 1s linear infinite;
        }

        .status-pending {
          color: var(--text-tertiary);
        }

        .task-header-info {
          flex: 1;
        }

        .task-title {
          font-size: var(--text-lg);
          font-weight: var(--weight-semibold);
          color: var(--text-primary);
        }

        .task-id {
          font-family: var(--font-mono);
          font-size: var(--text-sm);
          color: var(--text-tertiary);
        }

        .task-meta-grid {
          display: grid;
          grid-template-columns: repeat(2, 1fr);
          gap: var(--space-3);
        }

        .meta-item {
          display: flex;
          align-items: flex-start;
          gap: var(--space-2);
          padding: var(--space-3);
          background: var(--bg-tertiary);
          border-radius: var(--radius-md);
        }

        .meta-item .icon-sm {
          color: var(--text-tertiary);
          margin-top: 2px;
        }

        .meta-label {
          font-size: var(--text-xs);
          color: var(--text-tertiary);
          text-transform: uppercase;
          letter-spacing: 0.5px;
        }

        .meta-value {
          font-size: var(--text-sm);
          color: var(--text-primary);
          font-weight: var(--weight-medium);
        }

        .meta-value.score {
          font-family: var(--font-mono);
          font-weight: var(--weight-bold);
        }

        .task-section {
          margin-top: var(--space-2);
        }

        .section-title {
          font-size: var(--text-sm);
          font-weight: var(--weight-semibold);
          color: var(--text-secondary);
          margin-bottom: var(--space-2);
        }

        .task-code {
          padding: var(--space-3);
          background: var(--bg-tertiary);
          border: 1px solid var(--border-primary);
          border-radius: var(--radius-md);
          font-family: var(--font-mono);
          font-size: var(--text-sm);
          color: var(--text-primary);
          overflow-x: auto;
          white-space: pre-wrap;
          word-break: break-word;
          max-height: 200px;
          overflow-y: auto;
        }

        .task-code.error {
          border-color: var(--accent-danger);
          color: var(--accent-danger);
        }

        .task-section.error .section-title {
          color: var(--accent-danger);
        }

        .task-feedback {
          padding-top: var(--space-4);
          border-top: 1px solid var(--border-primary);
        }

        .task-actions {
          display: flex;
          justify-content: flex-end;
          padding-top: var(--space-4);
          border-top: 1px solid var(--border-primary);
        }

        .retry-button {
          padding: var(--space-2) var(--space-4);
          background: var(--accent-warning);
          border: none;
          border-radius: var(--radius-md);
          color: var(--bg-primary);
          font-weight: var(--weight-semibold);
          cursor: pointer;
          transition: opacity var(--transition-fast);
        }

        .retry-button:hover {
          opacity: 0.9;
        }
      `})]})},q_=({isOpen:e,onClose:t,specialist:n,onDelete:r,onViewTasks:i})=>{if(!n)return null;const s=l=>l>=.85?"var(--accent-primary)":l>=.7?"var(--accent-secondary)":l>=.5?"var(--accent-warning)":"var(--accent-danger)",a=()=>n.trend?n.trend>0?c.jsx(Xn,{className:"icon-sm trend-up"}):n.trend<0?c.jsx(Br,{className:"icon-sm trend-down"}):c.jsx(Ui,{className:"icon-sm"}):c.jsx(Ui,{className:"icon-sm"}),o="model"in n;return c.jsxs($r,{isOpen:e,onClose:t,title:"Specialist Details",size:"lg",children:[c.jsxs("div",{className:"specialist-detail",children:[c.jsxs("div",{className:"specialist-header",children:[c.jsx("div",{className:"specialist-avatar",children:c.jsx(Tr,{className:"icon-lg"})}),c.jsxs("div",{className:"specialist-header-info",children:[c.jsx("h3",{className:"specialist-name",children:n.name}),c.jsxs("div",{className:"specialist-id",children:["#",n.id]}),n.generation!==void 0&&c.jsxs(cs,{variant:"info",size:"sm",children:["Generation ",n.generation]})]}),c.jsx(gu,{status:n.status})]}),c.jsxs("div",{className:"score-display",children:[c.jsxs("div",{className:"score-main",children:[c.jsx("span",{className:"score-label",children:"Current Score"}),c.jsx("span",{className:"score-value",style:{color:s(n.score||0)},children:(n.score||0).toFixed(3)}),c.jsx("span",{className:"score-trend",children:a()})]}),c.jsx(us,{value:(n.score||0)*100,variant:(n.score||0)>=.85?"primary":(n.score||0)>=.7?"secondary":"warning"})]}),c.jsxs("div",{className:"stats-grid",children:[n.tasks_completed!==void 0&&c.jsxs("div",{className:"stat-item",children:[c.jsx(u1,{className:"icon"}),c.jsxs("div",{className:"stat-info",children:[c.jsx("span",{className:"stat-value",children:n.tasks_completed}),c.jsx("span",{className:"stat-label",children:"Tasks Completed"})]})]}),o&&n.success_rate!==void 0&&c.jsxs("div",{className:"stat-item",children:[c.jsx(za,{className:"icon"}),c.jsxs("div",{className:"stat-info",children:[c.jsxs("span",{className:"stat-value",children:[(n.success_rate*100).toFixed(1),"%"]}),c.jsx("span",{className:"stat-label",children:"Success Rate"})]})]}),o&&n.created_at&&c.jsxs("div",{className:"stat-item",children:[c.jsx(os,{className:"icon"}),c.jsxs("div",{className:"stat-info",children:[c.jsx("span",{className:"stat-value",children:new Date(n.created_at).toLocaleDateString()}),c.jsx("span",{className:"stat-label",children:"Created"})]})]})]}),o&&c.jsxs(c.Fragment,{children:[c.jsxs("div",{className:"detail-section",children:[c.jsx("h4",{className:"section-title",children:"Configuration"}),c.jsxs("div",{className:"config-grid",children:[c.jsxs("div",{className:"config-item",children:[c.jsx("span",{className:"config-label",children:"Model"}),c.jsx("span",{className:"config-value",children:n.model||"-"})]}),c.jsxs("div",{className:"config-item",children:[c.jsx("span",{className:"config-label",children:"Domain"}),c.jsx("span",{className:"config-value",children:n.domain||"-"})]}),n.temperature!==void 0&&c.jsxs("div",{className:"config-item",children:[c.jsx("span",{className:"config-label",children:"Temperature"}),c.jsx("span",{className:"config-value",children:n.temperature})]})]})]}),n.system_prompt&&c.jsxs("div",{className:"detail-section",children:[c.jsx("h4",{className:"section-title",children:"System Prompt"}),c.jsx("pre",{className:"prompt-preview",children:n.system_prompt})]})]}),c.jsxs("div",{className:"specialist-actions",children:[i&&c.jsx(ge,{variant:"secondary",onClick:i,children:"View Tasks"}),r&&c.jsx(ge,{variant:"danger",icon:ls,onClick:r,children:"Delete Specialist"})]})]}),c.jsx("style",{children:`
        .specialist-detail {
          display: flex;
          flex-direction: column;
          gap: var(--space-4);
        }

        .specialist-header {
          display: flex;
          align-items: center;
          gap: var(--space-3);
          padding-bottom: var(--space-4);
          border-bottom: 1px solid var(--border-primary);
        }

        .specialist-avatar {
          width: 56px;
          height: 56px;
          display: flex;
          align-items: center;
          justify-content: center;
          background: var(--accent-primary-dim);
          color: var(--accent-primary);
          border-radius: var(--radius-lg);
        }

        .specialist-header-info {
          flex: 1;
          display: flex;
          flex-direction: column;
          gap: var(--space-1);
        }

        .specialist-name {
          font-size: var(--text-xl);
          font-weight: var(--weight-semibold);
          color: var(--text-primary);
        }

        .specialist-id {
          font-family: var(--font-mono);
          font-size: var(--text-sm);
          color: var(--text-tertiary);
        }

        .score-display {
          padding: var(--space-4);
          background: var(--bg-tertiary);
          border-radius: var(--radius-lg);
        }

        .score-main {
          display: flex;
          align-items: center;
          gap: var(--space-3);
          margin-bottom: var(--space-3);
        }

        .score-label {
          font-size: var(--text-sm);
          color: var(--text-secondary);
        }

        .score-value {
          font-family: var(--font-mono);
          font-size: var(--text-2xl);
          font-weight: var(--weight-bold);
        }

        .score-trend {
          display: flex;
          align-items: center;
        }

        .trend-up {
          color: var(--accent-primary);
        }

        .trend-down {
          color: var(--accent-danger);
        }

        .stats-grid {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: var(--space-3);
        }

        .stat-item {
          display: flex;
          align-items: center;
          gap: var(--space-3);
          padding: var(--space-3);
          background: var(--bg-tertiary);
          border-radius: var(--radius-md);
        }

        .stat-item .icon {
          color: var(--text-tertiary);
        }

        .stat-info {
          display: flex;
          flex-direction: column;
        }

        .stat-value {
          font-size: var(--text-lg);
          font-weight: var(--weight-bold);
          color: var(--text-primary);
        }

        .stat-label {
          font-size: var(--text-xs);
          color: var(--text-tertiary);
        }

        .detail-section {
          margin-top: var(--space-2);
        }

        .section-title {
          font-size: var(--text-sm);
          font-weight: var(--weight-semibold);
          color: var(--text-secondary);
          margin-bottom: var(--space-2);
        }

        .config-grid {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: var(--space-2);
        }

        .config-item {
          padding: var(--space-2);
          background: var(--bg-tertiary);
          border-radius: var(--radius-sm);
        }

        .config-label {
          display: block;
          font-size: var(--text-xs);
          color: var(--text-tertiary);
          margin-bottom: var(--space-1);
        }

        .config-value {
          font-size: var(--text-sm);
          color: var(--text-primary);
          font-weight: var(--weight-medium);
        }

        .prompt-preview {
          padding: var(--space-3);
          background: var(--bg-tertiary);
          border: 1px solid var(--border-primary);
          border-radius: var(--radius-md);
          font-family: var(--font-mono);
          font-size: var(--text-sm);
          color: var(--text-primary);
          overflow-x: auto;
          white-space: pre-wrap;
          word-break: break-word;
          max-height: 150px;
          overflow-y: auto;
        }

        .specialist-actions {
          display: flex;
          justify-content: flex-end;
          gap: var(--space-2);
          padding-top: var(--space-4);
          border-top: 1px solid var(--border-primary);
        }
      `})]})},J_=({isOpen:e,onClose:t,onSubmit:n,domains:r=[],specialists:i=[],loading:s=!1})=>{const[a,o]=_.useState({name:"",description:"",priority:"normal"}),[l,u]=_.useState({}),d=(v,y)=>{o(g=>({...g,[v]:y})),l[v]&&u(g=>({...g,[v]:void 0}))},h=()=>{const v={};return a.name.trim()||(v.name="Task name is required"),a.description.trim()||(v.description="Description is required"),u(v),Object.keys(v).length===0},f=v=>{v.preventDefault(),h()&&(n==null||n(a))},p=()=>{o({name:"",description:"",priority:"normal"}),u({}),t()},m=a.domain?i.filter(v=>v.domain===a.domain):i;return c.jsxs($r,{isOpen:e,onClose:p,title:"Create New Task",size:"md",children:[c.jsxs("form",{onSubmit:f,className:"new-task-form",children:[c.jsx(mu,{label:"Task Name",placeholder:"Enter task name",value:a.name,onChange:v=>d("name",v.target.value),error:l.name,required:!0}),c.jsxs("div",{className:"form-group",children:[c.jsx("label",{className:"form-label",children:"Description"}),c.jsx("textarea",{className:`form-textarea ${l.description?"error":""}`,placeholder:"Describe the task in detail...",value:a.description,onChange:v=>d("description",v.target.value),rows:4}),l.description&&c.jsx("span",{className:"form-error",children:l.description})]}),c.jsxs("div",{className:"form-row",children:[c.jsxs("div",{className:"form-group",children:[c.jsx("label",{className:"form-label",children:"Domain (Optional)"}),c.jsx(zn,{value:a.domain||"",onChange:v=>{d("domain",v),d("specialist_id","")},options:[{value:"",label:"Auto-select"},...r.map(v=>({value:v.id,label:v.name}))],placeholder:"Select domain"})]}),c.jsxs("div",{className:"form-group",children:[c.jsx("label",{className:"form-label",children:"Priority"}),c.jsx(zn,{value:a.priority||"normal",onChange:v=>d("priority",v),options:[{value:"low",label:"Low"},{value:"normal",label:"Normal"},{value:"high",label:"High"}]})]})]}),m.length>0&&c.jsxs("div",{className:"form-group",children:[c.jsx("label",{className:"form-label",children:"Specialist (Optional)"}),c.jsx(zn,{value:a.specialist_id||"",onChange:v=>d("specialist_id",v),options:[{value:"",label:"Auto-select best specialist"},...m.map(v=>({value:v.id,label:v.name}))],placeholder:"Select specialist"})]}),c.jsxs("div",{className:"form-group",children:[c.jsxs("label",{className:"form-label",children:[c.jsx(Zm,{className:"icon-sm"}),"Input Data (Optional)"]}),c.jsx("textarea",{className:"form-textarea code",placeholder:"Enter any input data or code...",value:a.input||"",onChange:v=>d("input",v.target.value),rows:6})]}),c.jsxs("div",{className:"form-actions",children:[c.jsx(ge,{variant:"ghost",type:"button",onClick:p,children:"Cancel"}),c.jsx(ge,{variant:"primary",type:"submit",icon:rg,loading:s,children:"Create Task"})]})]}),c.jsx("style",{children:`
        .new-task-form {
          display: flex;
          flex-direction: column;
          gap: var(--space-4);
        }

        .form-group {
          display: flex;
          flex-direction: column;
          gap: var(--space-2);
        }

        .form-label {
          display: flex;
          align-items: center;
          gap: var(--space-2);
          font-size: var(--text-sm);
          font-weight: var(--weight-medium);
          color: var(--text-secondary);
        }

        .form-row {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: var(--space-4);
        }

        .form-textarea {
          padding: var(--space-3);
          background: var(--bg-tertiary);
          border: 1px solid var(--border-primary);
          border-radius: var(--radius-md);
          color: var(--text-primary);
          font-family: var(--font-sans);
          font-size: var(--text-sm);
          resize: vertical;
          min-height: 80px;
          transition: border-color var(--transition-fast);
        }

        .form-textarea:focus {
          outline: none;
          border-color: var(--accent-primary);
        }

        .form-textarea.code {
          font-family: var(--font-mono);
          font-size: var(--text-xs);
        }

        .form-textarea.error {
          border-color: var(--accent-danger);
        }

        .form-error {
          font-size: var(--text-xs);
          color: var(--accent-danger);
        }

        .form-actions {
          display: flex;
          justify-content: flex-end;
          gap: var(--space-2);
          padding-top: var(--space-4);
          border-top: 1px solid var(--border-primary);
        }
      `})]})},e2=({isOpen:e,onClose:t,budget:n,history:r=[],onUpdateLimit:i})=>{if(!n)return null;const s=n.used/n.daily_limit*100,a=n.remaining<n.daily_limit*.2,o=n.remaining<n.daily_limit*.1,l=()=>o?"var(--accent-danger)":a?"var(--accent-warning)":"var(--accent-primary)",u=h=>`$${h.toFixed(2)}`,d=h=>new Date(h).toLocaleDateString(void 0,{month:"short",day:"numeric"});return c.jsxs($r,{isOpen:e,onClose:t,title:"Budget Details",size:"lg",children:[c.jsxs("div",{className:"budget-detail",children:[c.jsxs("div",{className:"budget-main",children:[c.jsx("div",{className:"budget-icon",style:{background:`${l()}20`},children:c.jsx(Da,{className:"icon-lg",style:{color:l()}})}),c.jsxs("div",{className:"budget-info",children:[c.jsxs("div",{className:"budget-amounts",children:[c.jsx("span",{className:"amount-used",children:u(n.used)}),c.jsx("span",{className:"amount-separator",children:"/"}),c.jsx("span",{className:"amount-limit",children:u(n.daily_limit)})]}),c.jsx("div",{className:"budget-label",children:"Daily Budget Usage"})]}),(a||o)&&c.jsxs("div",{className:"budget-warning",children:[c.jsx(rc,{className:"icon",style:{color:l()}}),c.jsxs("span",{style:{color:l()},children:[o?"Critical":"Low"," budget"]})]})]}),c.jsxs("div",{className:"budget-progress-section",children:[c.jsx(us,{value:s,size:"lg",variant:o?"danger":a?"warning":"primary"}),c.jsxs("div",{className:"progress-labels",children:[c.jsx("span",{children:"0%"}),c.jsxs("span",{className:"remaining-text",children:[c.jsx("span",{style:{color:l()},children:u(n.remaining)})," ","remaining"]}),c.jsx("span",{children:"100%"})]})]}),c.jsxs("div",{className:"stats-row",children:[c.jsxs("div",{className:"stat-card",children:[c.jsx(br,{className:"icon"}),c.jsxs("div",{children:[c.jsx("div",{className:"stat-value",children:u(n.used)}),c.jsx("div",{className:"stat-label",children:"Spent Today"})]})]}),c.jsxs("div",{className:"stat-card",children:[c.jsx(gn,{className:"icon"}),c.jsxs("div",{children:[c.jsx("div",{className:"stat-value",children:n.reset_time||"00:00 UTC"}),c.jsx("div",{className:"stat-label",children:"Reset Time"})]})]}),n.trend!==void 0&&c.jsxs("div",{className:"stat-card",children:[n.trend>0?c.jsx(Xn,{className:"icon",style:{color:"var(--accent-danger)"}}):c.jsx(Br,{className:"icon",style:{color:"var(--accent-primary)"}}),c.jsxs("div",{children:[c.jsxs("div",{className:"stat-value",children:[Math.abs(n.trend),"%"]}),c.jsxs("div",{className:"stat-label",children:[n.trend>0?"Increase":"Decrease"," vs avg"]})]})]})]}),r.length>0&&c.jsxs("div",{className:"budget-history",children:[c.jsx("h4",{className:"section-title",children:"Recent History"}),c.jsx("div",{className:"history-list",children:r.slice(0,7).map((h,f)=>c.jsxs("div",{className:"history-item",children:[c.jsxs("div",{className:"history-date",children:[c.jsx(os,{className:"icon-xs"}),d(h.date)]}),c.jsx("div",{className:"history-bar",children:c.jsx("div",{className:"history-fill",style:{width:`${h.used/n.daily_limit*100}%`,background:h.used>n.daily_limit?"var(--accent-danger)":"var(--accent-primary)"}})}),c.jsx("div",{className:"history-amount",children:u(h.used)})]},f))})]}),i&&c.jsxs("div",{className:"budget-settings",children:[c.jsx("h4",{className:"section-title",children:"Budget Settings"}),c.jsxs("div",{className:"settings-row",children:[c.jsx("label",{className:"settings-label",children:"Daily Limit"}),c.jsx("div",{className:"limit-options",children:[5,10,20,50].map(h=>c.jsxs("button",{className:`limit-option ${n.daily_limit===h?"active":""}`,onClick:()=>i(h),children:["$",h]},h))})]})]})]}),c.jsx("style",{children:`
        .budget-detail {
          display: flex;
          flex-direction: column;
          gap: var(--space-5);
        }

        .budget-main {
          display: flex;
          align-items: center;
          gap: var(--space-4);
          padding: var(--space-4);
          background: var(--bg-tertiary);
          border-radius: var(--radius-lg);
        }

        .budget-icon {
          width: 64px;
          height: 64px;
          display: flex;
          align-items: center;
          justify-content: center;
          border-radius: var(--radius-lg);
        }

        .budget-info {
          flex: 1;
        }

        .budget-amounts {
          font-family: var(--font-mono);
          font-size: var(--text-2xl);
          font-weight: var(--weight-bold);
        }

        .amount-used {
          color: var(--text-primary);
        }

        .amount-separator {
          color: var(--text-tertiary);
          margin: 0 var(--space-2);
        }

        .amount-limit {
          color: var(--text-secondary);
        }

        .budget-label {
          font-size: var(--text-sm);
          color: var(--text-tertiary);
          margin-top: var(--space-1);
        }

        .budget-warning {
          display: flex;
          align-items: center;
          gap: var(--space-2);
          padding: var(--space-2) var(--space-3);
          background: var(--bg-secondary);
          border-radius: var(--radius-md);
          font-size: var(--text-sm);
          font-weight: var(--weight-medium);
        }

        .budget-progress-section {
          padding: var(--space-4);
          background: var(--bg-tertiary);
          border-radius: var(--radius-lg);
        }

        .progress-labels {
          display: flex;
          justify-content: space-between;
          margin-top: var(--space-2);
          font-size: var(--text-xs);
          color: var(--text-tertiary);
        }

        .remaining-text {
          color: var(--text-secondary);
        }

        .stats-row {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: var(--space-3);
        }

        .stat-card {
          display: flex;
          align-items: center;
          gap: var(--space-3);
          padding: var(--space-3);
          background: var(--bg-tertiary);
          border-radius: var(--radius-md);
        }

        .stat-card .icon {
          color: var(--text-tertiary);
        }

        .stat-value {
          font-size: var(--text-md);
          font-weight: var(--weight-bold);
          color: var(--text-primary);
        }

        .stat-label {
          font-size: var(--text-xs);
          color: var(--text-tertiary);
        }

        .budget-history {
          border-top: 1px solid var(--border-primary);
          padding-top: var(--space-4);
        }

        .section-title {
          font-size: var(--text-sm);
          font-weight: var(--weight-semibold);
          color: var(--text-secondary);
          margin-bottom: var(--space-3);
        }

        .history-list {
          display: flex;
          flex-direction: column;
          gap: var(--space-2);
        }

        .history-item {
          display: flex;
          align-items: center;
          gap: var(--space-3);
        }

        .history-date {
          display: flex;
          align-items: center;
          gap: var(--space-1);
          font-size: var(--text-xs);
          color: var(--text-tertiary);
          min-width: 70px;
        }

        .history-bar {
          flex: 1;
          height: 8px;
          background: var(--bg-tertiary);
          border-radius: var(--radius-full);
          overflow: hidden;
        }

        .history-fill {
          height: 100%;
          border-radius: var(--radius-full);
          transition: width var(--transition-normal);
        }

        .history-amount {
          font-family: var(--font-mono);
          font-size: var(--text-xs);
          color: var(--text-secondary);
          min-width: 50px;
          text-align: right;
        }

        .budget-settings {
          border-top: 1px solid var(--border-primary);
          padding-top: var(--space-4);
        }

        .settings-row {
          display: flex;
          align-items: center;
          justify-content: space-between;
        }

        .settings-label {
          font-size: var(--text-sm);
          color: var(--text-secondary);
        }

        .limit-options {
          display: flex;
          gap: var(--space-2);
        }

        .limit-option {
          padding: var(--space-2) var(--space-3);
          background: var(--bg-tertiary);
          border: 1px solid var(--border-primary);
          border-radius: var(--radius-md);
          color: var(--text-secondary);
          font-family: var(--font-mono);
          font-size: var(--text-sm);
          cursor: pointer;
          transition: all var(--transition-fast);
        }

        .limit-option:hover {
          border-color: var(--border-secondary);
          color: var(--text-primary);
        }

        .limit-option.active {
          background: var(--accent-primary-dim);
          border-color: var(--accent-primary);
          color: var(--accent-primary);
        }
      `})]})},yf={theme:"dark",autoRefresh:!0,refreshInterval:30,notifications:!0,soundEffects:!1,evaluationMode:"both",evolutionAutoStart:!0,budgetWarningThreshold:20},t2=({isOpen:e,onClose:t,settings:n,onSave:r,onReset:i})=>{const[s,a]=_.useState({...yf,...n}),[o,l]=_.useState(!1),u=(f,p)=>{a(m=>({...m,[f]:p})),l(!0)},d=()=>{r==null||r(s),l(!1),t()},h=()=>{a(yf),i==null||i(),l(!0)};return c.jsxs($r,{isOpen:e,onClose:t,title:"Settings",size:"md",children:[c.jsxs("div",{className:"settings-panel",children:[c.jsxs("div",{className:"settings-section",children:[c.jsxs("h4",{className:"section-title",children:[c.jsx(Jm,{className:"icon-sm"}),"Appearance"]}),c.jsxs("div",{className:"setting-row",children:[c.jsxs("div",{className:"setting-info",children:[c.jsx("label",{className:"setting-label",children:"Theme"}),c.jsx("span",{className:"setting-description",children:"Choose your preferred color scheme"})]}),c.jsx(zn,{value:s.theme,onChange:f=>u("theme",f),options:[{value:"dark",label:"Dark"},{value:"light",label:"Light"},{value:"system",label:"System"}]})]})]}),c.jsxs("div",{className:"settings-section",children:[c.jsxs("h4",{className:"section-title",children:[c.jsx(Fr,{className:"icon-sm"}),"Data Refresh"]}),c.jsxs("div",{className:"setting-row",children:[c.jsxs("div",{className:"setting-info",children:[c.jsx("label",{className:"setting-label",children:"Auto Refresh"}),c.jsx("span",{className:"setting-description",children:"Automatically refresh dashboard data"})]}),c.jsxs("label",{className:"toggle",children:[c.jsx("input",{type:"checkbox",checked:s.autoRefresh,onChange:f=>u("autoRefresh",f.target.checked)}),c.jsx("span",{className:"toggle-slider"})]})]}),s.autoRefresh&&c.jsxs("div",{className:"setting-row",children:[c.jsxs("div",{className:"setting-info",children:[c.jsx("label",{className:"setting-label",children:"Refresh Interval"}),c.jsx("span",{className:"setting-description",children:"How often to fetch new data"})]}),c.jsx(zn,{value:String(s.refreshInterval),onChange:f=>u("refreshInterval",Number(f)),options:[{value:"10",label:"10 seconds"},{value:"30",label:"30 seconds"},{value:"60",label:"1 minute"},{value:"300",label:"5 minutes"}]})]})]}),c.jsxs("div",{className:"settings-section",children:[c.jsxs("h4",{className:"section-title",children:[c.jsx(du,{className:"icon-sm"}),"Notifications"]}),c.jsxs("div",{className:"setting-row",children:[c.jsxs("div",{className:"setting-info",children:[c.jsx("label",{className:"setting-label",children:"Enable Notifications"}),c.jsx("span",{className:"setting-description",children:"Show alerts for important events"})]}),c.jsxs("label",{className:"toggle",children:[c.jsx("input",{type:"checkbox",checked:s.notifications,onChange:f=>u("notifications",f.target.checked)}),c.jsx("span",{className:"toggle-slider"})]})]}),c.jsxs("div",{className:"setting-row",children:[c.jsxs("div",{className:"setting-info",children:[c.jsx("label",{className:"setting-label",children:"Sound Effects"}),c.jsx("span",{className:"setting-description",children:"Play sounds for notifications"})]}),c.jsxs("label",{className:"toggle",children:[c.jsx("input",{type:"checkbox",checked:s.soundEffects,onChange:f=>u("soundEffects",f.target.checked)}),c.jsx("span",{className:"toggle-slider"})]})]})]}),c.jsxs("div",{className:"settings-section",children:[c.jsxs("h4",{className:"section-title",children:[c.jsx(Xi,{className:"icon-sm"}),"Evolution"]}),c.jsxs("div",{className:"setting-row",children:[c.jsxs("div",{className:"setting-info",children:[c.jsx("label",{className:"setting-label",children:"Evaluation Mode"}),c.jsx("span",{className:"setting-description",children:"How specialists are evaluated"})]}),c.jsx(zn,{value:s.evaluationMode,onChange:f=>u("evaluationMode",f),options:[{value:"scoring_committee",label:"Scoring Committee"},{value:"ai_council",label:"AI Council"},{value:"both",label:"Both"}]})]}),c.jsxs("div",{className:"setting-row",children:[c.jsxs("div",{className:"setting-info",children:[c.jsx("label",{className:"setting-label",children:"Auto-start Evolution"}),c.jsx("span",{className:"setting-description",children:"Automatically trigger evolution cycles"})]}),c.jsxs("label",{className:"toggle",children:[c.jsx("input",{type:"checkbox",checked:s.evolutionAutoStart,onChange:f=>u("evolutionAutoStart",f.target.checked)}),c.jsx("span",{className:"toggle-slider"})]})]}),c.jsxs("div",{className:"setting-row",children:[c.jsxs("div",{className:"setting-info",children:[c.jsx("label",{className:"setting-label",children:"Budget Warning (%)"}),c.jsx("span",{className:"setting-description",children:"Alert when budget falls below this"})]}),c.jsx(zn,{value:String(s.budgetWarningThreshold),onChange:f=>u("budgetWarningThreshold",Number(f)),options:[{value:"10",label:"10%"},{value:"20",label:"20%"},{value:"30",label:"30%"},{value:"50",label:"50%"}]})]})]}),c.jsxs("div",{className:"settings-actions",children:[c.jsx(ge,{variant:"ghost",onClick:h,children:"Reset to Defaults"}),c.jsxs("div",{className:"action-group",children:[c.jsx(ge,{variant:"ghost",onClick:t,children:"Cancel"}),c.jsx(ge,{variant:"primary",icon:tg,onClick:d,disabled:!o,children:"Save Changes"})]})]})]}),c.jsx("style",{children:`
        .settings-panel {
          display: flex;
          flex-direction: column;
          gap: var(--space-5);
        }

        .settings-section {
          padding-bottom: var(--space-4);
          border-bottom: 1px solid var(--border-primary);
        }

        .settings-section:last-of-type {
          border-bottom: none;
        }

        .section-title {
          display: flex;
          align-items: center;
          gap: var(--space-2);
          font-size: var(--text-sm);
          font-weight: var(--weight-semibold);
          color: var(--text-primary);
          margin-bottom: var(--space-3);
        }

        .setting-row {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: var(--space-3) 0;
        }

        .setting-info {
          flex: 1;
        }

        .setting-label {
          display: block;
          font-size: var(--text-sm);
          color: var(--text-primary);
          margin-bottom: var(--space-1);
        }

        .setting-description {
          font-size: var(--text-xs);
          color: var(--text-tertiary);
        }

        .toggle {
          position: relative;
          display: inline-block;
          width: 44px;
          height: 24px;
          cursor: pointer;
        }

        .toggle input {
          opacity: 0;
          width: 0;
          height: 0;
        }

        .toggle-slider {
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: var(--bg-tertiary);
          border: 1px solid var(--border-primary);
          border-radius: var(--radius-full);
          transition: all var(--transition-fast);
        }

        .toggle-slider::before {
          content: '';
          position: absolute;
          width: 18px;
          height: 18px;
          left: 2px;
          bottom: 2px;
          background: var(--text-tertiary);
          border-radius: 50%;
          transition: all var(--transition-fast);
        }

        .toggle input:checked + .toggle-slider {
          background: var(--accent-primary-dim);
          border-color: var(--accent-primary);
        }

        .toggle input:checked + .toggle-slider::before {
          transform: translateX(20px);
          background: var(--accent-primary);
        }

        .settings-actions {
          display: flex;
          justify-content: space-between;
          padding-top: var(--space-4);
          border-top: 1px solid var(--border-primary);
        }

        .action-group {
          display: flex;
          gap: var(--space-2);
        }
      `})]})},n2=({isOpen:e,onClose:t,entries:n=[],onRestore:r,onPermanentDelete:i,loading:s=!1})=>{const[a,o]=_.useState(""),[l,u]=_.useState(null),d=n.filter(p=>p.name.toLowerCase().includes(a.toLowerCase())||p.id.toLowerCase().includes(a.toLowerCase())),h=p=>new Date(p).toLocaleDateString(void 0,{year:"numeric",month:"short",day:"numeric"}),f=p=>p>=.85?"var(--accent-primary)":p>=.7?"var(--accent-secondary)":p>=.5?"var(--accent-warning)":"var(--accent-danger)";return c.jsxs($r,{isOpen:e,onClose:t,title:"Specialist Graveyard",size:"lg",children:[c.jsxs("div",{className:"graveyard-modal",children:[c.jsxs("div",{className:"graveyard-header",children:[c.jsx("div",{className:"header-icon",children:c.jsx(kr,{className:"icon-lg"})}),c.jsxs("div",{className:"header-info",children:[c.jsx("p",{className:"header-description",children:"Retired specialists that underperformed or were replaced by evolution. You can restore them or permanently delete them."}),c.jsxs(cs,{variant:"ghost",size:"sm",children:[n.length," retired specialists"]})]})]}),c.jsx("div",{className:"graveyard-search",children:c.jsx(mu,{placeholder:"Search by name or ID...",value:a,onChange:p=>o(p.target.value),icon:ng})}),c.jsx("div",{className:"graveyard-list",children:s?c.jsx("div",{className:"graveyard-loading",children:[...Array(3)].map((p,m)=>c.jsx("div",{className:"skeleton skeleton-card",style:{height:"80px"}},m))}):d.length===0?c.jsx("div",{className:"graveyard-empty",children:a?c.jsx("p",{children:"No specialists match your search."}):c.jsxs(c.Fragment,{children:[c.jsx(kr,{className:"icon-xl empty-icon"}),c.jsx("p",{children:"The graveyard is empty."}),c.jsx("p",{className:"empty-hint",children:"No specialists have been retired yet."})]})}):d.map(p=>c.jsxs("div",{className:`graveyard-entry ${l===p.id?"selected":""}`,onClick:()=>u(l===p.id?null:p.id),children:[c.jsx("div",{className:"entry-icon",children:c.jsx(Tr,{className:"icon"})}),c.jsxs("div",{className:"entry-info",children:[c.jsx("div",{className:"entry-name",children:p.name}),c.jsxs("div",{className:"entry-meta",children:[c.jsxs("span",{className:"entry-id",children:["#",p.id.slice(0,8)]}),p.generation!==void 0&&c.jsxs(c.Fragment,{children:[c.jsx("span",{className:"separator",children:"•"}),c.jsxs("span",{children:["Gen ",p.generation]})]})]})]}),c.jsxs("div",{className:"entry-stats",children:[c.jsxs("div",{className:"stat",children:[c.jsx("span",{className:"stat-value",style:{color:f(p.final_score||0)},children:(p.final_score||0).toFixed(3)}),c.jsx("span",{className:"stat-label",children:"Final Score"})]}),c.jsxs("div",{className:"stat",children:[c.jsx("span",{className:"stat-value",children:p.lifetime_tasks}),c.jsx("span",{className:"stat-label",children:"Tasks"})]})]}),c.jsxs("div",{className:"entry-date",children:[c.jsx(os,{className:"icon-xs"}),h(p.retired_at)]}),l===p.id&&c.jsxs("div",{className:"entry-details",children:[p.reason&&c.jsxs("div",{className:"entry-reason",children:[c.jsx("strong",{children:"Reason:"})," ",p.reason]}),c.jsxs("div",{className:"entry-actions",children:[r&&c.jsx(ge,{variant:"secondary",size:"sm",icon:Fr,onClick:m=>{m.stopPropagation(),r(p.id)},children:"Restore"}),i&&c.jsx(ge,{variant:"danger",size:"sm",icon:ls,onClick:m=>{m.stopPropagation(),i(p.id)},children:"Delete Forever"})]})]})]},p.id))})]}),c.jsx("style",{children:`
        .graveyard-modal {
          display: flex;
          flex-direction: column;
          gap: var(--space-4);
        }

        .graveyard-header {
          display: flex;
          gap: var(--space-4);
          padding: var(--space-4);
          background: var(--bg-tertiary);
          border-radius: var(--radius-lg);
        }

        .header-icon {
          width: 56px;
          height: 56px;
          display: flex;
          align-items: center;
          justify-content: center;
          background: var(--accent-danger-dim);
          color: var(--accent-danger);
          border-radius: var(--radius-lg);
          flex-shrink: 0;
        }

        .header-info {
          flex: 1;
        }

        .header-description {
          font-size: var(--text-sm);
          color: var(--text-secondary);
          margin-bottom: var(--space-2);
        }

        .graveyard-search {
          margin-bottom: var(--space-2);
        }

        .graveyard-list {
          display: flex;
          flex-direction: column;
          gap: var(--space-2);
          max-height: 400px;
          overflow-y: auto;
        }

        .graveyard-entry {
          display: flex;
          flex-wrap: wrap;
          align-items: center;
          gap: var(--space-3);
          padding: var(--space-3);
          background: var(--bg-tertiary);
          border: 1px solid var(--border-primary);
          border-radius: var(--radius-md);
          cursor: pointer;
          transition: all var(--transition-fast);
        }

        .graveyard-entry:hover {
          border-color: var(--border-secondary);
        }

        .graveyard-entry.selected {
          border-color: var(--accent-danger);
          background: var(--accent-danger-dim);
        }

        .entry-icon {
          width: 40px;
          height: 40px;
          display: flex;
          align-items: center;
          justify-content: center;
          background: var(--bg-secondary);
          border-radius: var(--radius-md);
          color: var(--text-tertiary);
        }

        .entry-info {
          flex: 1;
          min-width: 120px;
        }

        .entry-name {
          font-size: var(--text-sm);
          font-weight: var(--weight-medium);
          color: var(--text-primary);
        }

        .entry-meta {
          display: flex;
          gap: var(--space-1);
          font-size: var(--text-xs);
          color: var(--text-tertiary);
        }

        .entry-id {
          font-family: var(--font-mono);
        }

        .separator {
          color: var(--border-primary);
        }

        .entry-stats {
          display: flex;
          gap: var(--space-4);
        }

        .stat {
          text-align: center;
        }

        .stat-value {
          display: block;
          font-family: var(--font-mono);
          font-size: var(--text-sm);
          font-weight: var(--weight-bold);
          color: var(--text-primary);
        }

        .stat-label {
          font-size: var(--text-xs);
          color: var(--text-tertiary);
        }

        .entry-date {
          display: flex;
          align-items: center;
          gap: var(--space-1);
          font-size: var(--text-xs);
          color: var(--text-tertiary);
        }

        .entry-details {
          width: 100%;
          padding-top: var(--space-3);
          margin-top: var(--space-2);
          border-top: 1px solid var(--border-primary);
        }

        .entry-reason {
          font-size: var(--text-sm);
          color: var(--text-secondary);
          margin-bottom: var(--space-3);
        }

        .entry-actions {
          display: flex;
          gap: var(--space-2);
        }

        .graveyard-empty {
          display: flex;
          flex-direction: column;
          align-items: center;
          padding: var(--space-8);
          color: var(--text-tertiary);
          text-align: center;
        }

        .empty-icon {
          margin-bottom: var(--space-3);
          opacity: 0.5;
        }

        .empty-hint {
          font-size: var(--text-sm);
          margin-top: var(--space-2);
        }

        .graveyard-loading {
          display: flex;
          flex-direction: column;
          gap: var(--space-2);
        }
      `})]})},xf=()=>{var K,P;const{overview:e,domains:t,budget:n,recentTasks:r,evaluationMode:i,benchmarkStatus:s,health:a,loading:o,error:l,refetchAll:u,setEvaluationMode:d}=Y0(),h=V0(),f=Z0(),{lastRefresh:p,isRefreshing:m}=X0({interval:3e4,onRefresh:u,immediate:!1}),[v,y]=_.useState(null),[g,x]=_.useState(null),[b,k]=_.useState(!1),[w,j]=_.useState(!1),[S,N]=_.useState(!1),[T,E]=_.useState(!1),L=_.useCallback(async C=>{try{await d(C),f==null||f.success("Evaluation Mode Updated",`Mode set to ${C}`)}catch(D){f==null||f.error("Failed to update mode",D instanceof Error?D.message:"Unknown error")}},[d,f]),A=_.useCallback(async()=>{try{await h.run(),f==null||f.success("Benchmark Started","Running benchmark suite")}catch(C){f==null||f.error("Benchmark Failed",C instanceof Error?C.message:"Unknown error")}},[h,f]),q=_.useCallback(()=>{f==null||f.info("Evolution Triggered","Starting evolution cycle")},[f]),ve=((K=e==null?void 0:e.domains)==null?void 0:K.slice(0,1).map(()=>{const C=new Date;return Array.from({length:14},(D,I)=>({timestamp:new Date(C.getTime()-(13-I)*24*60*60*1e3).toISOString(),score:.7+Math.random()*.25,label:"Avg Score"}))})[0])||[],W=(r||[]).map(C=>({id:C.id,task_name:C.task_name,specialist_id:C.specialist_id,specialist_name:C.specialist_name,status:C.status,score:C.score,duration:C.execution_time,timestamp:C.timestamp})),U=(a==null?void 0:a.status)==="healthy"?"healthy":(a==null?void 0:a.status)==="degraded"?"degraded":"unhealthy";return l&&!e?c.jsxs("div",{className:"error-page",children:[c.jsxs("div",{className:"error-content",children:[c.jsx("div",{className:"error-icon",children:"⚠️"}),c.jsx("h2",{children:"Failed to Load Dashboard"}),c.jsx("p",{children:l.message}),c.jsxs("button",{className:"retry-button",onClick:u,children:[c.jsx(Yi,{className:"icon-sm"}),"Retry"]})]}),c.jsx("style",{children:`
          .error-page {
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            background: var(--bg-primary);
          }
          .error-content {
            text-align: center;
            padding: var(--space-8);
            background: var(--bg-secondary);
            border: 1px solid var(--border-primary);
            border-radius: var(--radius-lg);
            max-width: 400px;
          }
          .error-icon {
            font-size: 3rem;
            margin-bottom: var(--space-4);
          }
          .error-content h2 {
            color: var(--text-primary);
            margin-bottom: var(--space-2);
          }
          .error-content p {
            color: var(--text-secondary);
            margin-bottom: var(--space-4);
          }
          .retry-button {
            display: inline-flex;
            align-items: center;
            gap: var(--space-2);
            padding: var(--space-2) var(--space-4);
            background: var(--accent-primary);
            border: none;
            border-radius: var(--radius-md);
            color: var(--bg-primary);
            font-weight: var(--weight-semibold);
            cursor: pointer;
          }
        `})]}):c.jsxs("div",{className:"dashboard-layout",children:[c.jsx(In,{systemHealth:U,onSettingsClick:()=>N(!0),onBudgetClick:()=>j(!0)}),c.jsx(Fn,{activePage:"dashboard",domains:t==null?void 0:t.map(C=>{var D;return{id:C.name,name:C.name,icon:Tr,specialistCount:((D=C.specialists)==null?void 0:D.length)||0,avgScore:C.avg_score||0}}),onRunBenchmark:A,onForceEvolution:q,onNewTask:()=>k(!0),onViewGraveyard:()=>E(!0)}),c.jsxs(Bn,{children:[c.jsx(ds,{title:c.jsxs(c.Fragment,{children:[c.jsx(za,{className:"icon",style:{color:"var(--accent-primary)"}}),"Dashboard Overview"]}),subtitle:p?`Last updated: ${p.toLocaleTimeString()}`:void 0,actions:c.jsx("button",{className:"refresh-btn",onClick:u,disabled:m||o,children:c.jsx(Yi,{className:`icon-sm ${m?"spinning":""}`})})}),c.jsx(le,{children:c.jsxs(vo,{columns:4,children:[c.jsx(Te,{title:"Total Specialists",value:(e==null?void 0:e.total_specialists)??"-",icon:Tr,variant:"primary",loading:o}),c.jsx(Te,{title:"Active Domains",value:((P=e==null?void 0:e.domains)==null?void 0:P.length)??"-",icon:za,variant:"success",loading:o}),c.jsx(Te,{title:"Tasks Today",value:(e==null?void 0:e.total_tasks_today)??"-",icon:gn,trend:12,trendLabel:"vs yesterday",loading:o}),c.jsx(Te,{title:"Spent Today",value:n?`$${(n.production_spent_today||0).toFixed(2)}`:"-",icon:br,variant:n&&n.production_remaining<n.production_limit*.2?"warning":"default",loading:o})]})}),c.jsx(le,{title:"Evaluation Mode",children:c.jsx(v1,{value:i,onChange:L,disabled:o})}),c.jsx(le,{title:"Domain Pools",children:c.jsx("div",{className:"domain-grid",children:o?Array.from({length:3}).map((C,D)=>c.jsx("div",{className:"skeleton skeleton-card",style:{height:"160px"}},D)):t==null?void 0:t.map(C=>{var D;return c.jsx(x1,{domain:{name:C.name,specialists:typeof C.specialists=="number"?C.specialists:((D=C.specialists)==null?void 0:D.length)||0,avg_score:C.avg_score||0,best_score:C.best_score||0,tasks_today:C.tasks_today||0,convergence_progress:C.convergence_progress||0,evolution_paused:C.evolution_paused||!1},specialists:Array.isArray(C.specialists)?C.specialists.map(I=>({id:I.id,name:I.name,score:I.score,status:I.status,tasks_completed:I.tasks_completed,generation:I.generation})):[],onSpecialistClick:I=>x(I)},C.name)})})}),c.jsxs("div",{className:"two-column",children:[c.jsx(le,{title:"Score Trends",children:c.jsx(nv,{data:ve,height:280,title:"",fill:!0})}),c.jsx(le,{title:"Benchmarks",children:c.jsx(b1,{status:s||void 0,onStart:A,onPause:()=>h.pause(),loading:h.loading})})]}),c.jsx(le,{title:"Recent Tasks",children:c.jsx(lg,{tasks:W,loading:o,onViewTask:C=>y(C),emptyMessage:"No recent tasks"})}),c.jsx(le,{children:c.jsx(w1,{budget:n||void 0,onClick:()=>j(!0)})})]}),c.jsx(Z_,{isOpen:!!v,onClose:()=>y(null),task:v||void 0}),c.jsx(q_,{isOpen:!!g,onClose:()=>x(null),specialist:g||void 0}),c.jsx(J_,{isOpen:b,onClose:()=>k(!1),domains:t==null?void 0:t.map(C=>({id:C.name,name:C.name})),onSubmit:C=>{f==null||f.success("Task Created",`Created task: ${C.name}`),k(!1)}}),c.jsx(e2,{isOpen:w,onClose:()=>j(!1),budget:n||void 0}),c.jsx(t2,{isOpen:S,onClose:()=>N(!1),onSave:()=>{f==null||f.success("Settings Saved","Your preferences have been updated")}}),c.jsx(n2,{isOpen:T,onClose:()=>E(!1),entries:[]}),c.jsx("style",{children:`
        .dashboard-layout {
          min-height: 100vh;
          background: var(--bg-primary);
        }

        .domain-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
          gap: var(--space-4);
        }

        .two-column {
          display: grid;
          grid-template-columns: repeat(2, 1fr);
          gap: var(--space-6);
        }

        @media (max-width: 1024px) {
          .two-column {
            grid-template-columns: 1fr;
          }
        }

        .refresh-btn {
          display: flex;
          align-items: center;
          justify-content: center;
          width: 36px;
          height: 36px;
          background: var(--bg-tertiary);
          border: 1px solid var(--border-primary);
          border-radius: var(--radius-md);
          color: var(--text-secondary);
          cursor: pointer;
          transition: all var(--transition-fast);
        }

        .refresh-btn:hover:not(:disabled) {
          background: var(--bg-hover);
          color: var(--text-primary);
        }

        .refresh-btn:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .spinning {
          animation: spin 1s linear infinite;
        }
      `})]})},r2=[{id:"1",timestamp:"2024-01-15T10:30:00Z",category:"API Calls",description:"GPT-4 inference",amount:.42,specialist_name:"code-gen-v3",domain:"coding"},{id:"2",timestamp:"2024-01-15T11:15:00Z",category:"API Calls",description:"Claude evaluation",amount:.18,specialist_name:"eval-specialist",domain:"evaluation"},{id:"3",timestamp:"2024-01-15T12:00:00Z",category:"Embedding",description:"Document embedding",amount:.05,specialist_name:"doc-indexer",domain:"indexing"},{id:"4",timestamp:"2024-01-15T14:30:00Z",category:"API Calls",description:"GPT-4 inference",amount:.38,specialist_name:"code-review-v2",domain:"coding"},{id:"5",timestamp:"2024-01-15T15:45:00Z",category:"Evolution",description:"Specialist mutation",amount:.25,domain:"system"},{id:"6",timestamp:"2024-01-14T09:00:00Z",category:"API Calls",description:"Claude inference",amount:.22,specialist_name:"planning-v1",domain:"planning"},{id:"7",timestamp:"2024-01-14T10:30:00Z",category:"Benchmark",description:"HumanEval run",amount:.85,domain:"benchmark"},{id:"8",timestamp:"2024-01-14T13:00:00Z",category:"API Calls",description:"GPT-4 inference",amount:.45,specialist_name:"debug-specialist",domain:"coding"}],i2=["All","API Calls","Embedding","Evolution","Benchmark"],s2=()=>{var d;const[e,t]=_.useState("7d"),[n,r]=_.useState("All"),[i,s]=_.useState(""),a=_.useMemo(()=>{let h=[...r2];const f=new Date;if(e==="today"){const p=new Date(f.getFullYear(),f.getMonth(),f.getDate());h=h.filter(m=>new Date(m.timestamp)>=p)}else if(e==="7d"){const p=new Date(f.getTime()-6048e5);h=h.filter(m=>new Date(m.timestamp)>=p)}else if(e==="30d"){const p=new Date(f.getTime()-2592e6);h=h.filter(m=>new Date(m.timestamp)>=p)}if(n!=="All"&&(h=h.filter(p=>p.category===n)),i){const p=i.toLowerCase();h=h.filter(m=>{var v,y;return m.description.toLowerCase().includes(p)||((v=m.specialist_name)==null?void 0:v.toLowerCase().includes(p))||((y=m.domain)==null?void 0:y.toLowerCase().includes(p))})}return h.sort((p,m)=>new Date(m.timestamp).getTime()-new Date(p.timestamp).getTime())},[e,n,i]),o=_.useMemo(()=>{const h=a.reduce((m,v)=>m+v.amount,0),f=a.reduce((m,v)=>(m[v.category]=(m[v.category]||0)+v.amount,m),{}),p=a.length>0?h/a.length:0;return{total:h,byCategory:f,avgPerEntry:p,count:a.length}},[a]),l=()=>{const h=["Timestamp","Category","Description","Amount","Specialist","Domain"],f=a.map(g=>[g.timestamp,g.category,g.description,g.amount.toFixed(4),g.specialist_name||"",g.domain||""]),p=[h,...f].map(g=>g.join(",")).join(`
`),m=new Blob([p],{type:"text/csv"}),v=URL.createObjectURL(m),y=document.createElement("a");y.href=v,y.download=`cost-log-${new Date().toISOString().split("T")[0]}.csv`,y.click(),URL.revokeObjectURL(v)},u=h=>new Date(h).toLocaleString();return c.jsxs("div",{className:"dashboard-layout",children:[c.jsx(In,{systemHealth:"healthy"}),c.jsx(Fn,{activePage:"cost-log"}),c.jsxs(Bn,{children:[c.jsx(ds,{title:c.jsxs(c.Fragment,{children:[c.jsx(br,{className:"icon",style:{color:"var(--accent-warning)"}}),"Cost Log"]}),subtitle:"Track and analyze API usage costs",actions:c.jsxs("button",{className:"export-btn",onClick:l,children:[c.jsx(e1,{className:"icon-sm"}),"Export CSV"]})}),c.jsx(le,{children:c.jsxs(vo,{columns:4,children:[c.jsx(Te,{title:"Total Spent",value:`$${o.total.toFixed(2)}`,icon:br,variant:"warning"}),c.jsx(Te,{title:"Transactions",value:o.count,icon:Uo}),c.jsx(Te,{title:"Avg per Entry",value:`$${o.avgPerEntry.toFixed(3)}`,icon:br}),c.jsx(Te,{title:"Top Category",value:((d=Object.entries(o.byCategory).sort((h,f)=>f[1]-h[1])[0])==null?void 0:d[0])||"-",icon:Uo})]})}),c.jsx(le,{children:c.jsxs("div",{className:"filters-bar",children:[c.jsxs("div",{className:"filter-group",children:[c.jsx(os,{className:"icon-sm"}),c.jsxs("select",{value:e,onChange:h=>t(h.target.value),children:[c.jsx("option",{value:"today",children:"Today"}),c.jsx("option",{value:"7d",children:"Last 7 Days"}),c.jsx("option",{value:"30d",children:"Last 30 Days"}),c.jsx("option",{value:"all",children:"All Time"})]})]}),c.jsxs("div",{className:"filter-group",children:[c.jsx(Uo,{className:"icon-sm"}),c.jsx("select",{value:n,onChange:h=>r(h.target.value),children:i2.map(h=>c.jsx("option",{value:h,children:h},h))})]}),c.jsx("div",{className:"filter-group search",children:c.jsx("input",{type:"text",placeholder:"Search descriptions, specialists...",value:i,onChange:h=>s(h.target.value)})}),c.jsx("button",{className:"refresh-btn",onClick:()=>window.location.reload(),children:c.jsx(Yi,{className:"icon-sm"})})]})}),c.jsx(le,{title:"Cost Entries",children:c.jsx("div",{className:"cost-table-wrapper",children:c.jsxs("table",{className:"cost-table",children:[c.jsx("thead",{children:c.jsxs("tr",{children:[c.jsx("th",{children:"Timestamp"}),c.jsx("th",{children:"Category"}),c.jsx("th",{children:"Description"}),c.jsx("th",{children:"Specialist"}),c.jsx("th",{children:"Domain"}),c.jsx("th",{children:"Amount"})]})}),c.jsx("tbody",{children:a.length===0?c.jsx("tr",{children:c.jsx("td",{colSpan:6,className:"empty-row",children:"No cost entries found"})}):a.map(h=>c.jsxs("tr",{children:[c.jsx("td",{className:"timestamp",children:u(h.timestamp)}),c.jsx("td",{children:c.jsx("span",{className:`category-badge category-${h.category.toLowerCase().replace(/\s+/g,"-")}`,children:h.category})}),c.jsx("td",{children:h.description}),c.jsx("td",{children:h.specialist_name||"-"}),c.jsx("td",{children:h.domain||"-"}),c.jsxs("td",{className:"amount",children:["$",h.amount.toFixed(4)]})]},h.id))})]})})}),c.jsx(le,{title:"Cost by Category",children:c.jsx("div",{className:"category-breakdown",children:Object.entries(o.byCategory).sort((h,f)=>f[1]-h[1]).map(([h,f])=>c.jsxs("div",{className:"category-row",children:[c.jsx("span",{className:"category-name",children:h}),c.jsx("div",{className:"category-bar-container",children:c.jsx("div",{className:"category-bar",style:{width:`${o.total>0?f/o.total*100:0}%`}})}),c.jsxs("span",{className:"category-amount",children:["$",(f||0).toFixed(2)]}),c.jsxs("span",{className:"category-percent",children:[o.total>0?(f/o.total*100).toFixed(1):"0.0","%"]})]},h))})})]}),c.jsx("style",{children:a2})]})},a2=`
  .dashboard-layout {
    min-height: 100vh;
    background: var(--bg-primary);
  }

  .export-btn {
    display: flex;
    align-items: center;
    gap: var(--space-2);
    padding: var(--space-2) var(--space-4);
    background: var(--accent-primary);
    border: none;
    border-radius: var(--radius-md);
    color: var(--bg-primary);
    font-weight: var(--weight-semibold);
    cursor: pointer;
    transition: opacity var(--transition-fast);
  }

  .export-btn:hover {
    opacity: 0.9;
  }

  .filters-bar {
    display: flex;
    gap: var(--space-4);
    flex-wrap: wrap;
    align-items: center;
  }

  .filter-group {
    display: flex;
    align-items: center;
    gap: var(--space-2);
    background: var(--bg-secondary);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-md);
    padding: var(--space-2) var(--space-3);
  }

  .filter-group select,
  .filter-group input {
    background: transparent;
    border: none;
    color: var(--text-primary);
    font-size: var(--text-sm);
    outline: none;
  }

  .filter-group.search {
    flex: 1;
    min-width: 200px;
  }

  .filter-group.search input {
    width: 100%;
  }

  .refresh-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 36px;
    height: 36px;
    background: var(--bg-tertiary);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-md);
    color: var(--text-secondary);
    cursor: pointer;
    transition: all var(--transition-fast);
  }

  .refresh-btn:hover {
    background: var(--bg-hover);
    color: var(--text-primary);
  }

  .cost-table-wrapper {
    overflow-x: auto;
  }

  .cost-table {
    width: 100%;
    border-collapse: collapse;
    background: var(--bg-secondary);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-lg);
  }

  .cost-table th {
    padding: var(--space-3) var(--space-4);
    text-align: left;
    font-size: var(--text-xs);
    font-weight: var(--weight-semibold);
    color: var(--text-tertiary);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    background: var(--bg-tertiary);
    border-bottom: 1px solid var(--border-primary);
  }

  .cost-table td {
    padding: var(--space-3) var(--space-4);
    border-bottom: 1px solid var(--border-primary);
    font-size: var(--text-sm);
    color: var(--text-secondary);
  }

  .cost-table tbody tr:hover {
    background: var(--bg-hover);
  }

  .cost-table tbody tr:last-child td {
    border-bottom: none;
  }

  .cost-table .timestamp {
    font-family: var(--font-mono);
    font-size: var(--text-xs);
    color: var(--text-tertiary);
  }

  .cost-table .amount {
    font-family: var(--font-mono);
    font-weight: var(--weight-semibold);
    color: var(--accent-warning);
  }

  .empty-row {
    text-align: center;
    color: var(--text-tertiary);
    padding: var(--space-8) !important;
  }

  .category-badge {
    display: inline-block;
    padding: var(--space-1) var(--space-2);
    border-radius: var(--radius-sm);
    font-size: var(--text-xs);
    font-weight: var(--weight-medium);
    background: var(--bg-tertiary);
    color: var(--text-secondary);
  }

  .category-badge.category-api-calls {
    background: var(--accent-primary-dim);
    color: var(--accent-primary);
  }

  .category-badge.category-embedding {
    background: var(--accent-secondary-dim);
    color: var(--accent-secondary);
  }

  .category-badge.category-evolution {
    background: var(--accent-warning-dim);
    color: var(--accent-warning);
  }

  .category-badge.category-benchmark {
    background: var(--accent-danger-dim);
    color: var(--accent-danger);
  }

  .category-breakdown {
    display: flex;
    flex-direction: column;
    gap: var(--space-3);
  }

  .category-row {
    display: flex;
    align-items: center;
    gap: var(--space-4);
  }

  .category-name {
    width: 100px;
    font-size: var(--text-sm);
    color: var(--text-secondary);
  }

  .category-bar-container {
    flex: 1;
    height: 8px;
    background: var(--bg-tertiary);
    border-radius: var(--radius-full);
    overflow: hidden;
  }

  .category-bar {
    height: 100%;
    background: var(--accent-primary);
    border-radius: var(--radius-full);
    transition: width var(--transition-normal);
  }

  .category-amount {
    width: 70px;
    text-align: right;
    font-family: var(--font-mono);
    font-size: var(--text-sm);
    color: var(--text-primary);
  }

  .category-percent {
    width: 50px;
    text-align: right;
    font-size: var(--text-sm);
    color: var(--text-tertiary);
  }
`,Pt=[{id:"sp-001",name:"code-gen-v1",domain:"coding",generation:1,retired_at:"2024-01-10T08:00:00Z",reason:"Low performance",final_score:.45,tasks_completed:23,lifespan_days:5},{id:"sp-002",name:"debug-helper-v2",domain:"coding",generation:2,retired_at:"2024-01-12T14:30:00Z",reason:"Superseded by better variant",final_score:.68,tasks_completed:45,lifespan_days:8},{id:"sp-003",name:"doc-writer-v1",domain:"documentation",generation:1,retired_at:"2024-01-08T10:00:00Z",reason:"Low performance",final_score:.52,tasks_completed:12,lifespan_days:3},{id:"sp-004",name:"test-gen-v3",domain:"testing",generation:3,retired_at:"2024-01-14T16:00:00Z",reason:"Pool convergence",final_score:.71,tasks_completed:67,lifespan_days:12},{id:"sp-005",name:"refactor-v1",domain:"coding",generation:1,retired_at:"2024-01-05T09:00:00Z",reason:"Experimental variant",final_score:.38,tasks_completed:8,lifespan_days:2}],o2=()=>{const[e,t]=_.useState(""),[n,r]=_.useState("date"),i=Pt.filter(l=>l.name.toLowerCase().includes(e.toLowerCase())||l.domain.toLowerCase().includes(e.toLowerCase())).sort((l,u)=>n==="date"?new Date(u.retired_at).getTime()-new Date(l.retired_at).getTime():n==="score"?u.final_score-l.final_score:u.tasks_completed-l.tasks_completed),s={total:Pt.length,avgScore:Pt.length>0?Pt.reduce((l,u)=>l+u.final_score,0)/Pt.length:0,totalTasks:Pt.reduce((l,u)=>l+u.tasks_completed,0),avgLifespan:Pt.length>0?Pt.reduce((l,u)=>l+u.lifespan_days,0)/Pt.length:0},a=l=>new Date(l).toLocaleDateString(),o=l=>l>=.7?"var(--accent-primary)":l>=.5?"var(--accent-warning)":"var(--accent-danger)";return c.jsxs("div",{className:"dashboard-layout",children:[c.jsx(In,{systemHealth:"healthy"}),c.jsx(Fn,{activePage:"graveyard"}),c.jsxs(Bn,{children:[c.jsx(ds,{title:c.jsxs(c.Fragment,{children:[c.jsx(kr,{className:"icon",style:{color:"var(--text-tertiary)"}}),"Specialist Graveyard"]}),subtitle:"Retired and superseded specialists"}),c.jsx(le,{children:c.jsxs(vo,{columns:4,children:[c.jsx(Te,{title:"Total Retired",value:s.total,icon:kr}),c.jsx(Te,{title:"Avg Final Score",value:s.avgScore.toFixed(2),icon:Br,variant:"warning"}),c.jsx(Te,{title:"Total Tasks Run",value:s.totalTasks,icon:gn}),c.jsx(Te,{title:"Avg Lifespan",value:`${s.avgLifespan.toFixed(1)}d`,icon:gn})]})}),c.jsx(le,{children:c.jsxs("div",{className:"filters-bar",children:[c.jsxs("div",{className:"search-group",children:[c.jsx(ng,{className:"icon-sm"}),c.jsx("input",{type:"text",placeholder:"Search specialists...",value:e,onChange:l=>t(l.target.value)})]}),c.jsxs("div",{className:"sort-group",children:[c.jsx("span",{children:"Sort by:"}),c.jsxs("select",{value:n,onChange:l=>r(l.target.value),children:[c.jsx("option",{value:"date",children:"Retirement Date"}),c.jsx("option",{value:"score",children:"Final Score"}),c.jsx("option",{value:"tasks",children:"Tasks Completed"})]})]})]})}),c.jsx(le,{title:"Retired Specialists",children:c.jsx("div",{className:"graveyard-list",children:i.length===0?c.jsxs("div",{className:"empty-state",children:[c.jsx(kr,{className:"empty-icon"}),c.jsx("p",{children:"No retired specialists found"})]}):i.map(l=>c.jsxs("div",{className:"graveyard-card",children:[c.jsxs("div",{className:"card-header",children:[c.jsxs("div",{className:"specialist-info",children:[c.jsx("h3",{children:l.name}),c.jsx("span",{className:"domain-badge",children:l.domain}),c.jsxs("span",{className:"generation",children:["Gen ",l.generation]})]}),c.jsxs("div",{className:"card-actions",children:[c.jsx("button",{className:"action-btn",title:"Resurrect specialist",children:c.jsx(Fr,{className:"icon-sm"})}),c.jsx("button",{className:"action-btn danger",title:"Permanently delete",children:c.jsx(ls,{className:"icon-sm"})})]})]}),c.jsxs("div",{className:"card-stats",children:[c.jsxs("div",{className:"stat",children:[c.jsx("span",{className:"stat-label",children:"Final Score"}),c.jsx("span",{className:"stat-value",style:{color:o(l.final_score||0)},children:(l.final_score||0).toFixed(3)})]}),c.jsxs("div",{className:"stat",children:[c.jsx("span",{className:"stat-label",children:"Tasks"}),c.jsx("span",{className:"stat-value",children:l.tasks_completed})]}),c.jsxs("div",{className:"stat",children:[c.jsx("span",{className:"stat-label",children:"Lifespan"}),c.jsxs("span",{className:"stat-value",children:[l.lifespan_days,"d"]})]}),c.jsxs("div",{className:"stat",children:[c.jsx("span",{className:"stat-label",children:"Retired"}),c.jsx("span",{className:"stat-value",children:a(l.retired_at)})]})]}),c.jsxs("div",{className:"card-reason",children:[c.jsx("span",{className:"reason-label",children:"Reason:"}),c.jsx("span",{className:"reason-text",children:l.reason})]})]},l.id))})})]}),c.jsx("style",{children:l2})]})},l2=`
  .dashboard-layout {
    min-height: 100vh;
    background: var(--bg-primary);
  }

  .filters-bar {
    display: flex;
    gap: var(--space-4);
    flex-wrap: wrap;
    align-items: center;
  }

  .search-group {
    display: flex;
    align-items: center;
    gap: var(--space-2);
    background: var(--bg-secondary);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-md);
    padding: var(--space-2) var(--space-3);
    flex: 1;
    min-width: 200px;
  }

  .search-group input {
    background: transparent;
    border: none;
    color: var(--text-primary);
    font-size: var(--text-sm);
    outline: none;
    width: 100%;
  }

  .sort-group {
    display: flex;
    align-items: center;
    gap: var(--space-2);
    font-size: var(--text-sm);
    color: var(--text-secondary);
  }

  .sort-group select {
    background: var(--bg-secondary);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-md);
    padding: var(--space-2) var(--space-3);
    color: var(--text-primary);
    font-size: var(--text-sm);
  }

  .graveyard-list {
    display: flex;
    flex-direction: column;
    gap: var(--space-4);
  }

  .graveyard-card {
    background: var(--bg-secondary);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-lg);
    padding: var(--space-4);
    transition: border-color var(--transition-fast);
  }

  .graveyard-card:hover {
    border-color: var(--border-secondary);
  }

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: var(--space-3);
  }

  .specialist-info {
    display: flex;
    align-items: center;
    gap: var(--space-2);
    flex-wrap: wrap;
  }

  .specialist-info h3 {
    font-size: var(--text-base);
    color: var(--text-primary);
    margin: 0;
  }

  .domain-badge {
    padding: var(--space-1) var(--space-2);
    background: var(--bg-tertiary);
    border-radius: var(--radius-sm);
    font-size: var(--text-xs);
    color: var(--text-secondary);
  }

  .generation {
    font-size: var(--text-xs);
    color: var(--text-tertiary);
    font-family: var(--font-mono);
  }

  .card-actions {
    display: flex;
    gap: var(--space-2);
  }

  .action-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 32px;
    height: 32px;
    background: var(--bg-tertiary);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-md);
    color: var(--text-secondary);
    cursor: pointer;
    transition: all var(--transition-fast);
  }

  .action-btn:hover {
    background: var(--bg-hover);
    color: var(--text-primary);
  }

  .action-btn.danger:hover {
    background: var(--accent-danger-dim);
    border-color: var(--accent-danger);
    color: var(--accent-danger);
  }

  .card-stats {
    display: flex;
    gap: var(--space-6);
    margin-bottom: var(--space-3);
    flex-wrap: wrap;
  }

  .stat {
    display: flex;
    flex-direction: column;
    gap: var(--space-1);
  }

  .stat-label {
    font-size: var(--text-xs);
    color: var(--text-tertiary);
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .stat-value {
    font-size: var(--text-sm);
    font-weight: var(--weight-semibold);
    color: var(--text-primary);
    font-family: var(--font-mono);
  }

  .card-reason {
    padding-top: var(--space-3);
    border-top: 1px solid var(--border-primary);
    font-size: var(--text-sm);
  }

  .reason-label {
    color: var(--text-tertiary);
    margin-right: var(--space-2);
  }

  .reason-text {
    color: var(--text-secondary);
  }

  .empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: var(--space-12);
    color: var(--text-tertiary);
  }

  .empty-icon {
    width: 48px;
    height: 48px;
    margin-bottom: var(--space-4);
    opacity: 0.5;
  }
`,bf={theme:"dark",notifications:!0,autoRefresh:!0,refreshInterval:30,dailyBudgetLimit:50,budgetWarningThreshold:80,evolutionEnabled:!0,evolutionInterval:60,minPoolSize:3,maxPoolSize:10},c2=()=>{const[e,t]=_.useState(bf),[n,r]=_.useState(!1),i=(o,l)=>{t(u=>({...u,[o]:l})),r(!0)},s=()=>{console.log("Saving settings:",e),r(!1),alert("Settings saved successfully!")},a=()=>{t(bf),r(!0)};return c.jsxs("div",{className:"dashboard-layout",children:[c.jsx(In,{systemHealth:"healthy"}),c.jsx(Fn,{activePage:"settings"}),c.jsxs(Bn,{children:[c.jsx(ds,{title:c.jsxs(c.Fragment,{children:[c.jsx(ig,{className:"icon",style:{color:"var(--accent-secondary)"}}),"Settings"]}),subtitle:"Configure your JARVIS dashboard",actions:c.jsxs("div",{className:"header-actions",children:[c.jsxs("button",{className:"reset-btn",onClick:a,children:[c.jsx(Fr,{className:"icon-sm"}),"Reset"]}),c.jsxs("button",{className:"save-btn",onClick:s,disabled:!n,children:[c.jsx(tg,{className:"icon-sm"}),"Save Changes"]})]})}),c.jsx(le,{title:"Appearance",children:c.jsxs("div",{className:"settings-group",children:[c.jsxs("div",{className:"setting-row",children:[c.jsxs("div",{className:"setting-info",children:[c.jsx(Jm,{className:"setting-icon"}),c.jsxs("div",{children:[c.jsx("h4",{children:"Theme"}),c.jsx("p",{children:"Choose your preferred color scheme"})]})]}),c.jsxs("select",{value:e.theme,onChange:o=>i("theme",o.target.value),children:[c.jsx("option",{value:"dark",children:"Dark"}),c.jsx("option",{value:"light",children:"Light"}),c.jsx("option",{value:"system",children:"System"})]})]}),c.jsxs("div",{className:"setting-row",children:[c.jsxs("div",{className:"setting-info",children:[c.jsx(du,{className:"setting-icon"}),c.jsxs("div",{children:[c.jsx("h4",{children:"Notifications"}),c.jsx("p",{children:"Show desktop notifications for important events"})]})]}),c.jsxs("label",{className:"toggle",children:[c.jsx("input",{type:"checkbox",checked:e.notifications,onChange:o=>i("notifications",o.target.checked)}),c.jsx("span",{className:"toggle-slider"})]})]}),c.jsxs("div",{className:"setting-row",children:[c.jsxs("div",{className:"setting-info",children:[c.jsx(Xi,{className:"setting-icon"}),c.jsxs("div",{children:[c.jsx("h4",{children:"Auto-refresh"}),c.jsx("p",{children:"Automatically refresh dashboard data"})]})]}),c.jsxs("label",{className:"toggle",children:[c.jsx("input",{type:"checkbox",checked:e.autoRefresh,onChange:o=>i("autoRefresh",o.target.checked)}),c.jsx("span",{className:"toggle-slider"})]})]}),e.autoRefresh&&c.jsxs("div",{className:"setting-row sub-setting",children:[c.jsx("div",{className:"setting-info",children:c.jsxs("div",{children:[c.jsx("h4",{children:"Refresh Interval"}),c.jsx("p",{children:"How often to refresh data (seconds)"})]})}),c.jsx("input",{type:"number",value:e.refreshInterval,onChange:o=>i("refreshInterval",parseInt(o.target.value)||30),min:10,max:300})]})]})}),c.jsx(le,{title:"Budget",children:c.jsxs("div",{className:"settings-group",children:[c.jsxs("div",{className:"setting-row",children:[c.jsxs("div",{className:"setting-info",children:[c.jsx(br,{className:"setting-icon"}),c.jsxs("div",{children:[c.jsx("h4",{children:"Daily Budget Limit"}),c.jsx("p",{children:"Maximum daily spend in USD"})]})]}),c.jsxs("div",{className:"input-with-prefix",children:[c.jsx("span",{children:"$"}),c.jsx("input",{type:"number",value:e.dailyBudgetLimit,onChange:o=>i("dailyBudgetLimit",parseFloat(o.target.value)||50),min:1,step:1})]})]}),c.jsxs("div",{className:"setting-row",children:[c.jsxs("div",{className:"setting-info",children:[c.jsx(c1,{className:"setting-icon"}),c.jsxs("div",{children:[c.jsx("h4",{children:"Warning Threshold"}),c.jsx("p",{children:"Show warning when budget usage exceeds this percentage"})]})]}),c.jsxs("div",{className:"input-with-suffix",children:[c.jsx("input",{type:"number",value:e.budgetWarningThreshold,onChange:o=>i("budgetWarningThreshold",parseInt(o.target.value)||80),min:50,max:100}),c.jsx("span",{children:"%"})]})]})]})}),c.jsx(le,{title:"Evolution",children:c.jsxs("div",{className:"settings-group",children:[c.jsxs("div",{className:"setting-row",children:[c.jsxs("div",{className:"setting-info",children:[c.jsx(Xi,{className:"setting-icon"}),c.jsxs("div",{children:[c.jsx("h4",{children:"Auto Evolution"}),c.jsx("p",{children:"Automatically evolve specialist pools"})]})]}),c.jsxs("label",{className:"toggle",children:[c.jsx("input",{type:"checkbox",checked:e.evolutionEnabled,onChange:o=>i("evolutionEnabled",o.target.checked)}),c.jsx("span",{className:"toggle-slider"})]})]}),e.evolutionEnabled&&c.jsxs(c.Fragment,{children:[c.jsxs("div",{className:"setting-row sub-setting",children:[c.jsx("div",{className:"setting-info",children:c.jsxs("div",{children:[c.jsx("h4",{children:"Evolution Interval"}),c.jsx("p",{children:"Minutes between evolution cycles"})]})}),c.jsxs("div",{className:"input-with-suffix",children:[c.jsx("input",{type:"number",value:e.evolutionInterval,onChange:o=>i("evolutionInterval",parseInt(o.target.value)||60),min:15,max:1440}),c.jsx("span",{children:"min"})]})]}),c.jsxs("div",{className:"setting-row sub-setting",children:[c.jsx("div",{className:"setting-info",children:c.jsxs("div",{children:[c.jsx("h4",{children:"Pool Size Range"}),c.jsx("p",{children:"Min and max specialists per pool"})]})}),c.jsxs("div",{className:"range-inputs",children:[c.jsx("input",{type:"number",value:e.minPoolSize,onChange:o=>i("minPoolSize",parseInt(o.target.value)||3),min:1,max:e.maxPoolSize}),c.jsx("span",{children:"to"}),c.jsx("input",{type:"number",value:e.maxPoolSize,onChange:o=>i("maxPoolSize",parseInt(o.target.value)||10),min:e.minPoolSize,max:50})]})]})]})]})})]}),c.jsx("style",{children:u2})]})},u2=`
  .dashboard-layout {
    min-height: 100vh;
    background: var(--bg-primary);
  }

  .header-actions {
    display: flex;
    gap: var(--space-2);
  }

  .save-btn, .reset-btn {
    display: flex;
    align-items: center;
    gap: var(--space-2);
    padding: var(--space-2) var(--space-4);
    border: none;
    border-radius: var(--radius-md);
    font-weight: var(--weight-semibold);
    cursor: pointer;
    transition: all var(--transition-fast);
  }

  .save-btn {
    background: var(--accent-primary);
    color: var(--bg-primary);
  }

  .save-btn:hover:not(:disabled) {
    opacity: 0.9;
  }

  .save-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .reset-btn {
    background: var(--bg-tertiary);
    color: var(--text-secondary);
    border: 1px solid var(--border-primary);
  }

  .reset-btn:hover {
    background: var(--bg-hover);
    color: var(--text-primary);
  }

  .settings-group {
    background: var(--bg-secondary);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-lg);
    overflow: hidden;
  }

  .setting-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: var(--space-4);
    border-bottom: 1px solid var(--border-primary);
  }

  .setting-row:last-child {
    border-bottom: none;
  }

  .setting-row.sub-setting {
    padding-left: var(--space-8);
    background: var(--bg-tertiary);
  }

  .setting-info {
    display: flex;
    align-items: center;
    gap: var(--space-3);
  }

  .setting-icon {
    width: 20px;
    height: 20px;
    color: var(--text-tertiary);
  }

  .setting-info h4 {
    margin: 0;
    font-size: var(--text-sm);
    font-weight: var(--weight-medium);
    color: var(--text-primary);
  }

  .setting-info p {
    margin: var(--space-1) 0 0;
    font-size: var(--text-xs);
    color: var(--text-tertiary);
  }

  .setting-row select {
    padding: var(--space-2) var(--space-3);
    background: var(--bg-tertiary);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-md);
    color: var(--text-primary);
    font-size: var(--text-sm);
  }

  .setting-row input[type="number"] {
    width: 80px;
    padding: var(--space-2) var(--space-3);
    background: var(--bg-tertiary);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-md);
    color: var(--text-primary);
    font-size: var(--text-sm);
    text-align: center;
  }

  .input-with-prefix,
  .input-with-suffix {
    display: flex;
    align-items: center;
    gap: var(--space-2);
  }

  .input-with-prefix span,
  .input-with-suffix span {
    color: var(--text-tertiary);
    font-size: var(--text-sm);
  }

  .range-inputs {
    display: flex;
    align-items: center;
    gap: var(--space-2);
  }

  .range-inputs span {
    color: var(--text-tertiary);
    font-size: var(--text-sm);
  }

  /* Toggle Switch */
  .toggle {
    position: relative;
    display: inline-block;
    width: 48px;
    height: 24px;
  }

  .toggle input {
    opacity: 0;
    width: 0;
    height: 0;
  }

  .toggle-slider {
    position: absolute;
    cursor: pointer;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: var(--bg-tertiary);
    border: 1px solid var(--border-primary);
    border-radius: 24px;
    transition: all var(--transition-fast);
  }

  .toggle-slider:before {
    position: absolute;
    content: "";
    height: 18px;
    width: 18px;
    left: 2px;
    bottom: 2px;
    background-color: var(--text-tertiary);
    border-radius: 50%;
    transition: all var(--transition-fast);
  }

  .toggle input:checked + .toggle-slider {
    background-color: var(--accent-primary);
    border-color: var(--accent-primary);
  }

  .toggle input:checked + .toggle-slider:before {
    transform: translateX(24px);
    background-color: var(--bg-primary);
  }
`,d2=()=>{var h,f,p,m,v,y;const{name:e}=c0(),t=uu(),[n,r]=_.useState(null),[i,s]=_.useState(!0),[a,o]=_.useState(null);_.useEffect(()=>{if(!e)return;(async()=>{s(!0);try{const x=await Ve.dashboard.getDomainDetail(e);r(x),o(null)}catch(x){o(x instanceof Error?x:new Error("Failed to load domain"))}finally{s(!1)}})()},[e]);const l=Array.from({length:14},(g,x)=>{const b=new Date;return b.setDate(b.getDate()-(13-x)),{timestamp:b.toISOString(),score:.65+Math.random()*.3,label:"Avg Score"}}),u=((h=n==null?void 0:n.specialists)==null?void 0:h.map(g=>({id:g.id,name:g.name,score:g.score,status:g.status||"active",tasks_completed:g.tasks_completed||0,generation:g.generation,trend:Math.random()>.5?"up":"down"})))||[],d=[{id:"1",task_name:"Code review task",specialist_name:(f=u[0])==null?void 0:f.name,status:"completed",score:.89,duration:12.5,timestamp:new Date().toISOString()},{id:"2",task_name:"Debug session",specialist_name:(p=u[1])==null?void 0:p.name,status:"completed",score:.76,duration:8.2,timestamp:new Date(Date.now()-36e5).toISOString()},{id:"3",task_name:"Feature implementation",specialist_name:(m=u[0])==null?void 0:m.name,status:"running",duration:15,timestamp:new Date(Date.now()-72e5).toISOString()}];return i?c.jsxs("div",{className:"dashboard-layout",children:[c.jsx(In,{systemHealth:"healthy"}),c.jsx(Fn,{activePage:"dashboard"}),c.jsx(Bn,{children:c.jsxs("div",{className:"loading-state",children:[c.jsx(Yi,{className:"spinning"}),c.jsx("p",{children:"Loading domain..."})]})}),c.jsx("style",{children:ol})]}):a||!n?c.jsxs("div",{className:"dashboard-layout",children:[c.jsx(In,{systemHealth:"healthy"}),c.jsx(Fn,{activePage:"dashboard"}),c.jsx(Bn,{children:c.jsxs("div",{className:"error-state",children:[c.jsx("h2",{children:"Failed to load domain"}),c.jsx("p",{children:(a==null?void 0:a.message)||"Domain not found"}),c.jsxs("button",{onClick:()=>t("/"),children:[c.jsx(qd,{className:"icon-sm"}),"Back to Dashboard"]})]})}),c.jsx("style",{children:ol})]}):c.jsxs("div",{className:"dashboard-layout",children:[c.jsx(In,{systemHealth:"healthy"}),c.jsx(Fn,{activePage:"dashboard"}),c.jsxs(Bn,{children:[c.jsx(ds,{title:c.jsxs(c.Fragment,{children:[c.jsx("button",{className:"back-btn",onClick:()=>t("/"),children:c.jsx(qd,{className:"icon-sm"})}),c.jsx(Tr,{className:"icon",style:{color:"var(--accent-primary)"}}),n.name]}),subtitle:`Domain pool with ${((v=n.specialists)==null?void 0:v.length)||0} specialists`,actions:c.jsxs("div",{className:"header-actions",children:[c.jsxs("button",{className:"action-btn",children:[c.jsx(Xi,{className:"icon-sm"}),"Force Evolution"]}),c.jsxs("button",{className:"action-btn primary",children:[c.jsx(Yi,{className:"icon-sm"}),"Refresh"]})]})}),c.jsx(le,{children:c.jsxs(vo,{columns:4,children:[c.jsx(Te,{title:"Specialists",value:((y=n.specialists)==null?void 0:y.length)||0,icon:ic,variant:"primary"}),c.jsx(Te,{title:"Avg Score",value:(n.avg_score||0).toFixed(3),icon:Xn,variant:"success"}),c.jsx(Te,{title:"Best Score",value:(n.best_score||0).toFixed(3),icon:Xn}),c.jsx(Te,{title:"Tasks Today",value:n.tasks_today||0,icon:gn})]})}),c.jsx(le,{title:"Score Trend",children:c.jsx(nv,{data:l,height:300,title:"",fill:!0})}),c.jsx(le,{title:"Specialists",children:c.jsx("div",{className:"specialists-list",children:u.length===0?c.jsxs("div",{className:"empty-state",children:[c.jsx(ic,{className:"empty-icon"}),c.jsx("p",{children:"No specialists in this domain"})]}):u.map(g=>c.jsx(og,{specialist:g,onClick:()=>console.log("View specialist:",g.id)},g.id))})}),c.jsx(le,{title:"Recent Tasks",children:c.jsx(lg,{tasks:d,emptyMessage:"No recent tasks in this domain"})}),c.jsx(le,{title:"Evolution Status",children:c.jsxs("div",{className:"evolution-status",children:[c.jsxs("div",{className:"evolution-stat",children:[c.jsx("span",{className:"stat-label",children:"Convergence Progress"}),c.jsx("div",{className:"progress-bar",children:c.jsx("div",{className:"progress-fill",style:{width:`${(n.convergence_progress||0)*100}%`}})}),c.jsxs("span",{className:"stat-value",children:[((n.convergence_progress||0)*100).toFixed(1),"%"]})]}),c.jsxs("div",{className:"evolution-info",children:[c.jsxs("div",{className:"info-item",children:[c.jsx("span",{className:"info-label",children:"Evolution Status"}),c.jsx("span",{className:`info-value ${n.evolution_paused?"paused":"active"}`,children:n.evolution_paused?"Paused":"Active"})]}),c.jsxs("div",{className:"info-item",children:[c.jsx("span",{className:"info-label",children:"Generation"}),c.jsx("span",{className:"info-value",children:Math.max(...u.map(g=>g.generation||0),0)})]})]})]})})]}),c.jsx("style",{children:ol})]})},ol=`
  .dashboard-layout {
    min-height: 100vh;
    background: var(--bg-primary);
  }

  .back-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 32px;
    height: 32px;
    background: var(--bg-tertiary);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-md);
    color: var(--text-secondary);
    cursor: pointer;
    margin-right: var(--space-2);
    transition: all var(--transition-fast);
  }

  .back-btn:hover {
    background: var(--bg-hover);
    color: var(--text-primary);
  }

  .header-actions {
    display: flex;
    gap: var(--space-2);
  }

  .action-btn {
    display: flex;
    align-items: center;
    gap: var(--space-2);
    padding: var(--space-2) var(--space-4);
    background: var(--bg-tertiary);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-md);
    color: var(--text-secondary);
    font-weight: var(--weight-medium);
    cursor: pointer;
    transition: all var(--transition-fast);
  }

  .action-btn:hover {
    background: var(--bg-hover);
    color: var(--text-primary);
  }

  .action-btn.primary {
    background: var(--accent-primary);
    border-color: var(--accent-primary);
    color: var(--bg-primary);
  }

  .action-btn.primary:hover {
    opacity: 0.9;
  }

  .loading-state,
  .error-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 400px;
    color: var(--text-tertiary);
  }

  .loading-state .spinning {
    animation: spin 1s linear infinite;
    margin-bottom: var(--space-4);
  }

  .error-state h2 {
    color: var(--text-primary);
    margin-bottom: var(--space-2);
  }

  .error-state button {
    display: flex;
    align-items: center;
    gap: var(--space-2);
    margin-top: var(--space-4);
    padding: var(--space-2) var(--space-4);
    background: var(--accent-primary);
    border: none;
    border-radius: var(--radius-md);
    color: var(--bg-primary);
    cursor: pointer;
  }

  .specialists-list {
    display: flex;
    flex-direction: column;
    gap: var(--space-2);
  }

  .empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: var(--space-8);
    color: var(--text-tertiary);
  }

  .empty-icon {
    width: 48px;
    height: 48px;
    margin-bottom: var(--space-4);
    opacity: 0.5;
  }

  .evolution-status {
    background: var(--bg-secondary);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-lg);
    padding: var(--space-4);
  }

  .evolution-stat {
    display: flex;
    align-items: center;
    gap: var(--space-4);
    margin-bottom: var(--space-4);
  }

  .stat-label {
    font-size: var(--text-sm);
    color: var(--text-secondary);
    min-width: 150px;
  }

  .progress-bar {
    flex: 1;
    height: 8px;
    background: var(--bg-tertiary);
    border-radius: var(--radius-full);
    overflow: hidden;
  }

  .progress-fill {
    height: 100%;
    background: var(--accent-primary);
    border-radius: var(--radius-full);
    transition: width var(--transition-normal);
  }

  .stat-value {
    font-family: var(--font-mono);
    font-size: var(--text-sm);
    color: var(--text-primary);
    min-width: 60px;
    text-align: right;
  }

  .evolution-info {
    display: flex;
    gap: var(--space-8);
    padding-top: var(--space-4);
    border-top: 1px solid var(--border-primary);
  }

  .info-item {
    display: flex;
    flex-direction: column;
    gap: var(--space-1);
  }

  .info-label {
    font-size: var(--text-xs);
    color: var(--text-tertiary);
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .info-value {
    font-size: var(--text-sm);
    font-weight: var(--weight-semibold);
    color: var(--text-primary);
  }

  .info-value.active {
    color: var(--accent-primary);
  }

  .info-value.paused {
    color: var(--accent-warning);
  }

  @keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
  }
`,h2=()=>c.jsx(G0,{children:c.jsx(P0,{basename:"/ui",children:c.jsxs(N0,{children:[c.jsx(Yt,{path:"/",element:c.jsx(xf,{})}),c.jsx(Yt,{path:"/dashboard",element:c.jsx(xf,{})}),c.jsx(Yt,{path:"/cost-log",element:c.jsx(s2,{})}),c.jsx(Yt,{path:"/graveyard",element:c.jsx(o2,{})}),c.jsx(Yt,{path:"/settings",element:c.jsx(c2,{})}),c.jsx(Yt,{path:"/domain/:name",element:c.jsx(d2,{})}),c.jsx(Yt,{path:"*",element:c.jsx(j0,{to:"/",replace:!0})})]})})});ll.createRoot(document.getElementById("root")).render(c.jsx(Tf.StrictMode,{children:c.jsx(h2,{})}));
