"use strict";
// Sample planning content for the user-facing demo; separate from research data.
const IDEAS = [
  {id:'stress_self',goal:'stress',style:'self_directed',minutes:5,title:'Put a little down on paper',description:'Give the thoughts on your mind a place to land. There is no right way to begin.',steps:['Find a note or a piece of paper.','Write down what is taking up space in your day.','Circle one thing you would like to come back to later.']},
  {id:'stress_guided',goal:'stress',style:'guided',minutes:5,title:'Make a small pause your own',description:'Plan a quiet moment with something familiar: a favorite song, a view, or a little time away from your to-do list.',steps:['Choose a place where you feel comfortable.','Pick one small thing you would enjoy doing there.','Set aside a moment for it when it suits you.']},
  {id:'stress_social',goal:'stress',style:'social',minutes:15,title:'Make time for a catch-up',description:'Think of someone you enjoy talking to and make a little room to connect.',steps:['Choose someone you would like to catch up with.','Send a message to find a time that suits you both.','Keep the plan simple and comfortable.']},
  {id:'sleep_self',goal:'sleep',style:'self_directed',minutes:5,title:'Sketch your kind of evening',description:'Choose one familiar thing you would like to make room for as your day comes to a close.',steps:['Think about an evening activity you enjoy.','Write down one small way to make space for it.','Keep the plan easy enough for an ordinary day.']},
  {id:'sleep_guided',goal:'sleep',style:'guided',minutes:5,title:'Leave a note for tomorrow',description:'Take a few minutes to put tomorrow’s reminders in one place, ready for when you need them.',steps:['Write down tomorrow’s important reminders.','Choose one priority, leaving room for the unexpected.','Put the note somewhere you will find it.']},
  {id:'sleep_social',goal:'sleep',style:'social',minutes:15,title:'Plan a quieter evening together',description:'Talk with someone you share your evenings with about a routine you would both enjoy.',steps:['Find a moment that works for both of you.','Share one thing you each enjoy in the evening.','Choose a small plan you would like to try together.']},
  {id:'activity_self',goal:'activity',style:'self_directed',minutes:5,title:'Find movement you look forward to',description:'Start with what you enjoy. Make a short list of activities that suit your interests and comfort.',steps:['Write down two activities you already enjoy.','Consider the time, space and equipment each needs.','Pick an option that feels practical for your day.']},
  {id:'activity_guided',goal:'activity',style:'guided',minutes:5,title:'Make a little space in your day',description:'Choose a time and place for an activity you already know and feel comfortable doing.',steps:['Look for a free moment in your schedule.','Choose a familiar activity that fits.','Write down the time and anything you want to have ready.']},
  {id:'activity_social',goal:'activity',style:'social',minutes:15,title:'Plan something with a friend',description:'Bring a little company to an activity you both enjoy, with a plan that fits both of you.',steps:['Choose someone you would enjoy making plans with.','Ask what activity and pace feel comfortable for them.','Agree on a time and leave room to change the plan.']},
  {id:'nutrition_self',goal:'nutrition',style:'self_directed',minutes:5,title:'Make tomorrow’s meal a little easier',description:'Pick a familiar meal you enjoy and note what you already have for it.',steps:['Choose a meal that suits your own dietary needs.','Check the ingredients you already have.','Make a short list of anything else you need.']},
  {id:'nutrition_guided',goal:'nutrition',style:'guided',minutes:5,title:'Keep a few favorites close',description:'Build a small list of familiar meals to return to when you do not want to start from scratch.',steps:['Write down two or three meals you enjoy.','Note the time and ingredients each usually needs.','Choose one that fits your next busy day.']},
  {id:'nutrition_social',goal:'nutrition',style:'social',minutes:15,title:'Make a meal plan together',description:'Share the planning with someone you enjoy spending time with.',steps:['Ask what each person would like to prepare.','Account for everyone’s own dietary needs and preferences.','Choose a familiar option and divide the planning tasks.']}
];
const KEY = 'my-health-friend:user-space:v1';
const LABELS = {stress:'finding some calm',sleep:'winding down',activity:'making room to move',nutrition:'planning with care'};
const STYLES = {self_directed:'On your own',guided:'A little structure',social:'With someone'};
const defaultState = () => ({goal:'stress',minutes:5,style:'self_directed',saved:[],ratings:{}});
let state = defaultState();
try {
  const stored = JSON.parse(localStorage.getItem(KEY));
  if (stored && typeof stored === 'object') {
    if (Object.hasOwn(LABELS, stored.goal)) state.goal = stored.goal;
    if ([5,20].includes(stored.minutes)) state.minutes = stored.minutes;
    if (Object.hasOwn(STYLES, stored.style)) state.style = stored.style;
    if (Array.isArray(stored.saved)) state.saved = [...new Set(stored.saved)].filter(id => IDEAS.some(idea => idea.id === id));
    if (stored.ratings && typeof stored.ratings === 'object') IDEAS.forEach(idea => { if ([0,1].includes(stored.ratings[idea.id])) state.ratings[idea.id] = stored.ratings[idea.id]; });
  }
} catch { /* Unavailable or old browser storage falls back to this visit. */ }
function persist() {
  try { localStorage.setItem(KEY, JSON.stringify(state)); }
  catch { document.getElementById('feedback-message').textContent = 'Your choices are available for this visit. This browser could not save them for later.'; }
}
function node(tag, text, className) {
  const element = document.createElement(tag);
  if (text !== undefined) element.textContent = text;
  if (className) element.className = className;
  return element;
}
function button(text, className, action) {
  const element = node('button',text,className);
  element.type = 'button';
  element.addEventListener('click',action);
  return element;
}
function syncControls() {
  document.querySelectorAll('[data-goal]').forEach(b => {const active=b.dataset.goal===state.goal;b.classList.toggle('selected',active);b.setAttribute('aria-pressed',String(active));});
  document.querySelectorAll('[data-minutes]').forEach(b => {const active=Number(b.dataset.minutes)===state.minutes;b.classList.toggle('selected',active);b.setAttribute('aria-pressed',String(active));});
  document.getElementById('preferred-style').value=state.style;
}
function renderSaved() {
  const list=document.getElementById('saved-list');list.replaceChildren();
  document.getElementById('saved-count').textContent=state.saved.length;
  if (!state.saved.length) {list.append(node('p','Save an idea you like. It will be waiting for you here.','empty-state'));return;}
  state.saved.forEach(id => {
    const idea=IDEAS.find(item=>item.id===id), row=node('div',undefined,'saved-item'), label=node('div');
    label.append(node('strong',idea.title),node('small',`${idea.minutes} minutes · ${STYLES[idea.style]}`));
    const remove=button('Remove',undefined,()=>{state.saved=state.saved.filter(value=>value!==id);persist();renderSaved();syncSaveButtons();});
    remove.setAttribute('aria-label',`Remove ${idea.title} from saved ideas`);row.append(label,remove);list.append(row);
  });
}
function syncSaveButtons() {
  document.querySelectorAll('[data-save]').forEach(b => {const saved=state.saved.includes(b.dataset.save);b.setAttribute('aria-pressed',String(saved));b.querySelector('span').textContent=saved?'Saved':'Save';b.setAttribute('aria-label',`${saved?'Unsave':'Save'} ${IDEAS.find(i=>i.id===b.dataset.save).title}`);});
}
function score(idea) {return (idea.style===state.style?0.3:0)+(state.ratings[idea.id]===1?0.7:state.ratings[idea.id]===0?-0.7:0);}
function renderIdeas() {
  const list=document.getElementById('recommendation-grid');list.replaceChildren();
  const ideas=IDEAS.filter(idea=>idea.goal===state.goal&&idea.minutes<=state.minutes).sort((a,b)=>score(b)-score(a)||a.id.localeCompare(b.id)).slice(0,2);
  document.getElementById('match-tag').textContent=state.minutes===5?'5-minute ideas':'Within your time';
  document.getElementById('match-description').textContent=`A little inspiration for ${LABELS[state.goal]}, with your available time in mind.`;
  ideas.forEach((idea,index)=>{
    const card=node('article',undefined,'idea-card');card.dataset.idea=idea.id;
    const top=node('div',undefined,'idea-top');top.append(node('span',index===0?'A place to begin':'Another way to start','idea-label'));
    const save=button('', 'save-button',()=>{state.saved=state.saved.includes(idea.id)?state.saved.filter(id=>id!==idea.id):[...state.saved,idea.id];persist();renderSaved();syncSaveButtons();});
    save.dataset.save=idea.id;
    const icon=document.createElementNS('http://www.w3.org/2000/svg','svg');icon.setAttribute('viewBox','0 0 20 24');icon.setAttribute('aria-hidden','true');
    const path=document.createElementNS('http://www.w3.org/2000/svg','path');path.setAttribute('d','M4 3h12v17l-6-4-6 4Z');icon.append(path);save.append(icon,node('span','Save'));top.append(save);
    card.append(top,node('h3',idea.title),node('p',idea.description,'idea-description'));
    card.append(node('p',state.ratings[idea.id]===1?'An idea you found helpful':STYLES[idea.style],'idea-reason'));
    const bottom=node('div',undefined,'idea-bottom'),details=node('div',undefined,'idea-details');details.hidden=true;details.id=`details-${idea.id}`;
    const start=button('Try this idea','start-button',()=>{details.hidden=!details.hidden;start.setAttribute('aria-expanded',String(!details.hidden));start.firstChild.textContent=details.hidden?'Try this idea':'Close steps';});
    start.append(node('span','\u2192'));start.setAttribute('aria-expanded','false');start.setAttribute('aria-controls',details.id);bottom.append(node('span',`${idea.minutes} minutes`,'idea-duration'),start);card.append(bottom);
    const steps=node('ol');idea.steps.forEach(step=>steps.append(node('li',step)));details.append(steps);
    const ratings=node('div',undefined,'rating-row');ratings.append(node('span','Does this feel useful?'));
    [[1,'Helpful'],[0,'Not for me']].forEach(([rating,label])=>{
      const rate=button(label,undefined,()=>{
        state.ratings[idea.id]=rating;
        ratings.querySelectorAll('button').forEach(b=>b.setAttribute('aria-pressed',String(Number(b.dataset.rating)===rating)));
        document.getElementById('feedback-message').textContent='Thanks. Your feedback will help sort your next set of ideas.';persist();
      });rate.dataset.rating=rating;rate.setAttribute('aria-pressed',String(state.ratings[idea.id]===rating));ratings.append(rate);
    });details.append(ratings);card.append(details);list.append(card);
  });syncSaveButtons();
}

document.querySelectorAll('[data-goal]').forEach(b=>b.addEventListener('click',()=>{state.goal=b.dataset.goal;syncControls();persist();}));
document.querySelectorAll('[data-minutes]').forEach(b=>b.addEventListener('click',()=>{state.minutes=Number(b.dataset.minutes);syncControls();persist();}));
document.getElementById('preferred-style').addEventListener('change',event=>{state.style=event.target.value;persist();});
document.getElementById('find-ideas').addEventListener('click',()=>{renderIdeas();document.getElementById('feedback-message').textContent='Your ideas are ready.';document.getElementById('ideas-section').scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth',block:'start'});});
const dialog=document.getElementById('about-dialog');
['about-button','footer-about'].forEach(id=>document.getElementById(id).addEventListener('click',()=>dialog.showModal()));
document.getElementById('close-about').addEventListener('click',()=>dialog.close());
dialog.addEventListener('click',event=>{if(event.target===dialog){const r=dialog.getBoundingClientRect();if(event.clientX<r.left||event.clientX>r.right||event.clientY<r.top||event.clientY>r.bottom)dialog.close();}});
document.getElementById('reset-preferences').addEventListener('click',()=>{state=defaultState();persist();syncControls();renderIdeas();renderSaved();dialog.close();document.getElementById('feedback-message').textContent='Your choices and saved ideas have been reset.';});
syncControls();renderIdeas();renderSaved();
