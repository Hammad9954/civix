
const T={
en:{
  brand:"CIVIC SENSE",detect:"Detect",issues:"Issues",city:"City Pulse",reports:"Reports",admin:"Authority",assistant:"AI Assistant",
  hero:"AI POWERED CIVIC INTELLIGENCE",heroText:"See what your city needs. Upload a street image and Civic Sense automatically analyses it for common civic issues.",start:"START DETECTION ↗",
  detectTitle:"DETECT & REPORT.",detectSub:"Upload an image and our YOLO AI models will classify and score it automatically.",
  upload:"DROP AN IMAGE",choose:"CHOOSE IMAGE",analysing:"ANALYSING IMAGE…",ready:"IMAGE READY",result:"AI ANALYSIS RESULT",noResult:"Upload an image to begin.",
  map:"CITY MAP",mapSub:"Live civic issues and repair hotspots.",locate:"USE MY LOCATION",recentReports:"RECENT REPORTS",
  garbage:"Garbage",pothole:"Pothole",road:"Road Damage",light:"Street Light",water:"Waterlogging",
  submitReport:"SUBMIT CIVIC REPORT",priority:"Priority",department:"Department",status:"Status"
},
hi:{
  brand:"सिविक सेंस",detect:"पता लगाएं",issues:"समस्याएं",city:"शहर स्थिति",reports:"रिपोर्ट",admin:"प्राधिकरण",assistant:"AI सहायक",
  hero:"AI आधारित नागरिक तकनीक",heroText:"जानें कि आपके शहर को क्या चाहिए। तस्वीर अपलोड करें और सिविक सेंस सामान्य नागरिक समस्याओं का विश्लेषण करेगा।",start:"डिटेक्शन शुरू करें ↗",
  detectTitle:"पता लगाएं और रिपोर्ट करें.",detectSub:"तस्वीर अपलोड करें और हमारे YOLO AI मॉडल इसका स्वतः विश्लेषण करेंगे।",
  upload:"तस्वीर डालें",choose:"तस्वीर चुनें",analysing:"विश्लेषण हो रहा है…",ready:"तस्वीर तैयार",result:"AI विश्लेषण परिणाम",noResult:"शुरू करने के लिए तस्वीर अपलोड करें।",
  map:"शहर का नक्शा",mapSub:"लाइव नागरिक समस्याएं और मरम्मत केंद्र।",locate:"मेरी लोकेशन",recentReports:"हाल की रिपोर्ट",
  garbage:"कचरा",pothole:"गड्ढा",road:"सड़क क्षति",light:"स्ट्रीट लाइट",water:"जलभराव",
  submitReport:"नागरिक रिपोर्ट दर्ज करें",priority:"प्राथमिकता",department:"विभाग",status:"स्थिति"
},
mr:{
  brand:"सिविक सेन्स",detect:"शोधा",issues:"समस्या",city:"शहर स्थिती",reports:"अहवाल",admin:"प्राधिकरण",assistant:"AI सहाय्यक",
  hero:"AI आधारित नागरी तंत्रज्ञान",heroText:"तुमच्या शहराला काय हवे आहे ते पहा. प्रतिमा अपलोड करा आणि सिविक सेन्स सामान्य नागरी समस्या आपोआप तपासेल.",start:"डिटेक्शन सुरू करा ↗",
  detectTitle:"शोधा आणि नोंदवा.",detectSub:"प्रतिमा अपलोड करा आणि आमचे YOLO AI मॉडेल आपोआप विश्लेषण करतील.",
  upload:"प्रतिमा टाका",choose:"प्रतिमा निवडा",analysing:"विश्लेषण सुरू आहे…",ready:"प्रतिमा तयार",result:"AI विश्लेषण परिणाम",noResult:"सुरू करण्यासाठी प्रतिमा अपलोड करा.",
  map:"शहर नकाशा",mapSub:"थेट नागरी समस्या आणि दुरुस्ती ठिकाणे.",locate:"माझे स्थान",recentReports:"अलीकडील अहवाल",
  garbage:"कचरा",pothole:"खड्डा",road:"रस्त्याचे नुकसान",light:"स्ट्रीट लाईट",water:"पाणी साचणे",
  submitReport:"नागरी तक्रार नोंदवा",priority:"प्राधान्य",department:"विभाग",status:"स्थिती"
}
};
const fallback={en:T.en,hi:T.hi,mr:T.mr};
let lang=localStorage.getItem("cs-lang")||"en";
function tr(key){return (T[lang]||T.en)[key]||(T.en[key]||key)}
function applyLang(){
 document.querySelectorAll("[data-t]").forEach(e=>e.textContent=tr(e.dataset.t));
 document.documentElement.lang=lang; localStorage.setItem("cs-lang",lang);
 const s=document.getElementById("language"); if(s)s.value=lang;
}
function theme(){
 document.body.classList.toggle("dark",localStorage.getItem("cs-theme")==="dark");
 const b=document.getElementById("theme"); if(b)b.textContent=document.body.classList.contains("dark")?"☀":"☾";
}
function toast(x){const e=document.getElementById("toast");if(!e)return;e.textContent=x;e.classList.add("show");setTimeout(()=>e.classList.remove("show"),2400)}
document.addEventListener("DOMContentLoaded",()=>{
 theme();applyLang();
 document.getElementById("theme")?.addEventListener("click",()=>{localStorage.setItem("cs-theme",document.body.classList.contains("dark")?"light":"dark");theme()});
 document.getElementById("language")?.addEventListener("change",e=>{lang=e.target.value;applyLang()});
});


// ===== Civic Sense cinematic interactions =====
function initMotion(){
  const revealTargets=[...document.querySelectorAll('main>section,.title,.ticker')];
  const io=new IntersectionObserver((entries)=>entries.forEach(entry=>{if(entry.isIntersecting){entry.target.classList.add('revealed');io.unobserve(entry.target)}}),{threshold:.08});
  revealTargets.forEach((el,i)=>{el.style.transitionDelay=Math.min(i*.06,.36)+'s';io.observe(el)});

  const stage=document.querySelector('.motion-stage');
  if(stage && window.matchMedia('(pointer:fine)').matches){
    const cards=[...stage.querySelectorAll('.floatCard')];
    stage.addEventListener('mousemove',e=>{
      const r=stage.getBoundingClientRect(), x=(e.clientX-r.left)/r.width-.5, y=(e.clientY-r.top)/r.height-.5;
      cards.forEach(card=>{const d=Number(card.dataset.depth||2);card.style.marginLeft=(-x*d*10)+'px';card.style.marginTop=(-y*d*10)+'px';card.style.rotate=(x*d*2)+'deg'});
      const core=stage.querySelector('.visualCore'); if(core) core.style.transform=`translate(${x*-12}px,${y*-12}px)`;
    });
    stage.addEventListener('mouseleave',()=>{cards.forEach(card=>{card.style.marginLeft='';card.style.marginTop='';card.style.rotate=''});const core=stage.querySelector('.visualCore');if(core)core.style.transform=''});
  }

  document.querySelectorAll('.card,.stat,.issue,.report').forEach((el,i)=>el.style.animationDelay=(Math.min(i*55,500))+'ms');
}
document.addEventListener('DOMContentLoaded',initMotion);
