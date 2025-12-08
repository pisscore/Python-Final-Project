# DEAD HANDS - Blackjack but you bet with lives (Inspired by Buckshot roulette and old flash games)
# Uses async/threading for smooth card animations + the ability to run better
# fmt: off
# ^ I have autoformatting, threw in enumeration to run faster/remove the clutter of loops/functions
import pygame,asyncio,threading,random,math
from enum import Enum,auto

pygame.init()
W,H=900,700
BLACK,WHITE,GRAY_D,GRAY_M,GRAY_L,OFF_WHITE,GOLD=(0,0,0),(255,255,255),(30,30,30),(80,80,80),(150,150,150),(220,220,220),(255,215,0)
NAMES=["DEATH","REAPER","PHANTOM","WRAITH","SHADE","SPECTRE","HOLLOW","GRIM","MORTIS","VOID","RAVEN","OMEN","BANE","DREAD","MALICE"]
DIFF_COLORS=[(50,200,50),(120,200,50),(200,200,50),(200,120,50),(200,50,50)]
TAUNTS=["Let's see what you've got.","You won't last long.","Getting tired yet?","I don't lose.","This is the end."]

# Game states
class State(Enum):
 MENU=auto();BET=auto();DEAL=auto();PLAYER=auto();DEALER=auto();RESULT=auto();OVER=auto();WIN=auto();DYING=auto();NEXT=auto();HELP=auto();PAUSE=auto();EMOTE=auto()

# Card with rank and face
class Card:
 RANKS=['A','2','3','4','5','6','7','8','9','10','J','Q','K']
 def __init__(s,rank):s.rank,s.face_up=rank,True
 @property
 def value(s):return 10 if s.rank>=10 else 11 if s.rank==0 else s.rank+1

# Deck Size
class Deck:
 def __init__(s):s.reset()
 def reset(s):s.cards=[Card(r)for r in range(13)for _ in range(4)];random.shuffle(s.cards)
 def draw(s):
  if len(s.cards)<10:s.reset()
  return s.cards.pop()

# Value Calculation with current card hand
class Hand:
 def __init__(s):s.cards=[]
 def add(s,card):s.cards.append(card)
 def clear(s):s.cards.clear()
 @property
 def value(s):
  total=sum(c.value for c in s.cards if c.face_up);aces=sum(1 for c in s.cards if c.rank==0 and c.face_up)
  while total>21 and aces:total-=10;aces-=1
  return total
 @property
 def is_bust(s):return s.value>21
 @property
 def is_blackjack(s):return len(s.cards)==2 and s.value==21

# Dealer opponent
class Dealer:
 def __init__(s,threshold):s.threshold,s.lives,s.hand,s.blinking,s.blink_t,s.name=threshold,5,Hand(),False,0,random.choice(NAMES)

def hex_pts(cx,cy,r):return[(cx+r*math.cos(math.radians(60*i-30)),cy+r*math.sin(math.radians(60*i-30)))for i in range(6)]

# Main game class
class Game:
 def __init__(s):
  s.screen=pygame.display.set_mode((W,H));pygame.display.set_caption("DEAD HANDS")
  s.clock,s.font_h,s.font_l,s.font_m,s.font_s,s.font_c=pygame.time.Clock(),*[pygame.font.Font(None,x)for x in[120,72,48,32,36]]
  s.deck,s.player,s.lives,s.bet,s.stages=Deck(),Hand(),5,1,[19,18,17,16,15]
  s.dealers,s.dealer,s.d_idx,s.has_save=[],None,0,False
  s.state,s.prev,s.msg,s.msg_t,s.shake,s.flash,s.time=State.MENU,State.MENU,"",0,0,0,0
  s.title_a,s.death_t,s.death_p,s.btns,s.running,s.konami,s.cheat,s.react,s.react_t=150,0,[],[],True,[],False,0,0
  s.win_t,s.has_won=0,False
  s.loop=asyncio.new_event_loop();threading.Thread(target=lambda:(asyncio.set_event_loop(s.loop),s.loop.run_forever()),daemon=True).start()

 def new_game(s):s.dealers=[Dealer(t)for t in s.stages];s.dealer,s.d_idx,s.lives,s.bet,s.title_a=s.dealers[0],0,5,1,150;s.player.clear();s.dealer.hand.clear();s.has_save=True;s.state=State.BET;s.show_msg(f'"{TAUNTS[0]}"',0)
 def clear(s):s.player.clear();s.dealer.hand.clear()
 def show_msg(s,m,shake=0):s.msg,s.msg_t,s.shake=m,60,shake;s.flash=3 if shake else 0

 def check_end(s):
  if s.lives<=0:
   if s.state!=State.OVER:s.state=State.OVER;s.has_save=False;s.show_msg("YOU DIED",10)
  elif s.dealer.lives<=0:s.start_death()
  else:s.state=State.RESULT

 # Using async for smoother card computations/animations
 async def deal(s):
  s.state=State.DEAL;s.title_a=0;await asyncio.sleep(0.2)
  for i in range(4):
   card=s.deck.draw()
   if i%2==0:s.player.add(card)
   else:
    if i==3:card.face_up=False
    s.dealer.hand.add(card)
   await asyncio.sleep(0.15)
  if s.player.is_blackjack:
   s.dealer.hand.cards[1].face_up=True;await asyncio.sleep(0.3)
   if s.dealer.hand.is_blackjack:s.show_msg("PUSH",2)
   else:s.dealer.lives-=s.bet;s.lives+=1 if s.lives<5 else 0;s.show_msg("BLACKJACK!"+(" +1 LIFE"if s.lives<6 else""),5)
   s.check_end()
  else:s.state=State.PLAYER

 async def hit(s):
  s.player.add(s.deck.draw());await asyncio.sleep(0.15)
  if s.player.is_bust:s.dealer.hand.cards[1].face_up=True;s.lives-=s.bet;s.show_msg("BUST",8);await asyncio.sleep(0.4);s.check_end()
  elif s.player.value==21:s.dealer.lives-=s.bet;s.lives+=1 if s.lives<5 else 0;s.show_msg("21! +1 LIFE"if s.lives<6 else"21!",5);s.check_end()

 async def dealer_turn(s):
  s.state=State.DEALER;s.dealer.hand.cards[1].face_up=True;await asyncio.sleep(0.4);pv=s.player.value
  while s.dealer.hand.value<s.dealer.threshold and s.dealer.hand.value<pv:await asyncio.sleep(random.uniform(0.3,0.6));s.dealer.hand.add(s.deck.draw());await asyncio.sleep(0.15)
  await asyncio.sleep(0.2);s.resolve()

 def resolve(s):
  pv,dv=s.player.value,s.dealer.hand.value
  if s.dealer.hand.is_bust or pv>dv:s.dealer.lives-=s.bet;s.lives+=1 if pv==21 and s.lives<5 else 0;s.show_msg("21! +1 LIFE"if pv==21 and s.lives<6 else"YOU WIN",3 if pv!=21 else 5)
  elif dv>pv:s.lives-=s.bet;s.show_msg("YOU LOSE",6)
  else:s.show_msg("PUSH",2)
  s.check_end()

 # Death animation
 def start_death(s):s.state=State.DYING;s.death_t=0;cx,cy=W//2,180;s.death_p=[[cx+random.randint(-40,40),cy+random.randint(-60,60),random.uniform(-2,2),random.uniform(-3,-1),random.randint(3,8),255]for _ in range(50)]

 def draw_death(s):
  s.death_t+=1;fade=max(0,255-s.death_t*4);cx,cy=W//2,180
  if fade>0:
   sf=pygame.Surface((200,200),pygame.SRCALPHA);pygame.draw.ellipse(sf,(*GRAY_D,fade),(50,40,100,120))
   if fade>100:
    for ox in[80,120]:pygame.draw.circle(sf,(255,255,255,fade),(ox,90),6);pygame.draw.circle(sf,(0,0,0,fade),(ox,90),3)
   pygame.draw.line(sf,(*GRAY_L,fade),(80,140),(120,140),2);s.screen.blit(sf,(cx-100,cy-100))
  for p in s.death_p:p[0]+=p[2];p[1]+=p[3];p[3]+=0.1;p[5]=max(0,p[5]-5);pygame.draw.circle(s.screen,(int(p[5]),)*3,(int(p[0]),int(p[1])),p[4])if p[5]>0 else 0
  if s.death_t>60:
   s.d_idx+=1
   if s.d_idx>=len(s.dealers):s.state=State.WIN;s.has_save=False;s.has_won=True;s.win_t=0
   else:s.dealer=s.dealers[s.d_idx];s.clear();s.state=State.NEXT;s.show_msg(f'"{TAUNTS[s.d_idx]}"',0)

 # Drawing
 def draw_dealer(s):
  cx,cy,br,d=W//2,180,math.sin(s.time*3)*3,s.dealer;pygame.draw.ellipse(s.screen,GRAY_D,(cx-50,cy-70+br,100,120));pygame.draw.ellipse(s.screen,GRAY_M,(cx-50,cy-70+br,100,120),2)
  ey=int(cy-20+br);by=ey-12;pv,dv=s.player.value,d.hand.value;dying=s.state==State.DYING;inround=s.state in[State.RESULT,State.OVER,State.NEXT,State.DYING];won=inround and(dv>pv or s.player.is_bust)and not d.hand.is_bust and not dying;lost=inround and(d.hand.is_bust or(pv>dv and not s.player.is_bust))and not dying;angry=s.react==3 and s.react_t>0;happy=s.react==1 and s.react_t>0;sad=s.react==2 and s.react_t>0
  if not d.blinking:[pygame.draw.circle(s.screen,c,(cx+ox,ey+oy),r)for ox in[-20,20]for c,oy,r in[(WHITE,0,8 if dying else 6),(BLACK,2 if won else(-2 if(lost or dying)else 0),3)]]
  my=cy+30+br
  if dying:[pygame.draw.line(s.screen,GRAY_L,(cx+ox-8,by-3),(cx+ox+8,by+3),2)for ox in[-20,20]];pygame.draw.ellipse(s.screen,GRAY_L,(cx-10,my,20,12),2)
  elif angry:pygame.draw.line(s.screen,GRAY_L,(cx-28,by-5),(cx-12,by+2),2);pygame.draw.line(s.screen,GRAY_L,(cx+12,by+2),(cx+28,by-5),2);pygame.draw.arc(s.screen,GRAY_L,(cx-20,my,40,15),0,3.14,2)
  elif happy or won:[pygame.draw.line(s.screen,GRAY_L,(cx+ox-8,by+3),(cx+ox+8,by-3),2)for ox in[-20,20]];pygame.draw.arc(s.screen,GRAY_L,(cx-20,my-5,40,15),3.14,0,2)
  elif sad or lost:[pygame.draw.line(s.screen,GRAY_L,(cx+ox-8,by-3),(cx+ox+8,by+3),2)for ox in[-20,20]];pygame.draw.arc(s.screen,GRAY_L,(cx-20,my,40,15),0,3.14,2)
  else:[pygame.draw.line(s.screen,GRAY_L,(cx+ox-8,by),(cx+ox+8,by),2)for ox in[-20,20]];pygame.draw.line(s.screen,GRAY_L,(cx-20,int(my)),(cx+20,int(my)),2)
  pygame.draw.polygon(s.screen,GRAY_D,[(cx-80,cy+80+br),(cx+80,cy+80+br),(cx+120,H//2),(cx-120,H//2)]);[pygame.draw.line(s.screen,GRAY_M,(cx+ox,cy+60+br),(cx,cy+90+br),2)for ox in[-30,30]]
  t=s.font_c.render(d.name,True,GRAY_L);s.screen.blit(t,t.get_rect(center=(cx,cy-90+br)))

 def draw_diff(s):
  for i in range(5):pygame.draw.polygon(s.screen,DIFF_COLORS[i]if i<=s.d_idx else GRAY_D,hex_pts(W-200+i*35,35,14));pygame.draw.polygon(s.screen,WHITE,hex_pts(W-200+i*35,35,14),2)

 def draw_card(s,c,x,y):
  if c.face_up:pygame.draw.rect(s.screen,OFF_WHITE,(x,y,70,100));pygame.draw.rect(s.screen,BLACK,(x,y,70,100),2);t=s.font_c.render(Card.RANKS[c.rank],True,BLACK);s.screen.blit(t,t.get_rect(center=(x+35,y+50)))
  else:pygame.draw.rect(s.screen,GRAY_D,(x,y,70,100));pygame.draw.rect(s.screen,WHITE,(x,y,70,100),2);[pygame.draw.line(s.screen,GRAY_M,(x+i,y),(x+i,y+100),1)for i in range(0,70,10)];[pygame.draw.line(s.screen,GRAY_M,(x,y+i),(x+70,y+i),1)for i in range(0,100,10)]

 def draw_hand(s,h,y,sv=True):
  if not h.cards:return
  tw,sx=len(h.cards)*80-10,(W-len(h.cards)*80+10)//2;[s.draw_card(c,sx+i*80,y)for i,c in enumerate(h.cards)]
  if sv:s.screen.blit(s.font_c.render(str(h.value),True,WHITE),(sx+tw+20,y+35))

 def draw_lives(s):
  s.screen.blit(s.font_c.render("YOU",True,GRAY_L),(50,H-90));[pygame.draw.circle(s.screen,WHITE if i<s.lives else GRAY_M,(50+i*30,H-50),10,0 if i<s.lives else 2)for i in range(5)]
  s.screen.blit(s.font_c.render(s.dealer.name,True,GRAY_L),(50,20));[pygame.draw.circle(s.screen,WHITE if i<s.dealer.lives else GRAY_M,(50+i*30,60),10,0 if i<s.dealer.lives else 2)for i in range(5)]

 def draw_menu(s,mp):
  t1=s.font_l.render("DEAD HANDS",True,WHITE);t2=s.font_c.render("There are 5 people ahead of you, good luck.",True,GRAY_M);s.screen.blit(t1,t1.get_rect(center=(W//2,150)));s.screen.blit(t2,t2.get_rect(center=(W//2,220)));s.screen.blit(s.font_c.render("by GC",True,GRAY_D),(W-70,H-30));btns=[]
  for y,txt,cond in[(300,"NEW GAME",True),(380,"CONTINUE",s.has_save),(460,"HELP",True),(540,"QUIT",True)]:r=pygame.Rect(W//2-150,y,300,60);hov=r.collidepoint(mp)and cond;c=WHITE if hov else GRAY_L if cond else GRAY_D;pygame.draw.rect(s.screen,c,r,2);t=s.font_m.render(txt,True,c);s.screen.blit(t,t.get_rect(center=r.center));btns.append((r,txt,cond))
  if s.has_save:
   for i in range(5):pygame.draw.polygon(s.screen,DIFF_COLORS[i]if i<=s.d_idx else GRAY_D,hex_pts(W//2+180+i*28,410,10));pygame.draw.polygon(s.screen,WHITE,hex_pts(W//2+180+i*28,410,10),2)
  if s.has_won:
   cx,cy,r=W//2+230,150,20;pts=[(cx+r*math.cos(math.radians(90+i*72))*(.4 if i%2 else 1),cy-r*math.sin(math.radians(90+i*72))*(.4 if i%2 else 1))for i in range(10)]
   pygame.draw.polygon(s.screen,GOLD,pts)
  return btns

 def draw_help(s,mp):
  s.screen.fill(BLACK);[pygame.draw.rect(s.screen,(i//5,)*3,(i*2,i*2,W-i*4,H-i*4),1)for i in range(50)];t=s.font_l.render("HELP",True,WHITE);s.screen.blit(t,t.get_rect(center=(W//2,60)));y=120
  for sec,items in[("CONTROLS",[("H","Hit"),("S","Stand"),("SPACE","Deal/Continue"),("ESC","Pause")]),("DIFFICULTY",[("Green","Stands 19"),("Yellow","Stands 17-18"),("Red","Stands 15")]),("RULES",[("Bet","1-5 lives"),("21","Restores 1 life"),("Win","Deplete 5 dealer lives")])]:s.screen.blit(s.font_m.render(sec,True,GRAY_L),(100,y));y+=35;[(s.screen.blit(s.font_c.render(k,True,WHITE),(120,y)),s.screen.blit(s.font_c.render(v,True,GRAY_M),(250,y)),y:=y+28)for k,v in items];y+=20
  r=pygame.Rect(W//2-100,H-100,200,50);hov=r.collidepoint(mp);c=WHITE if hov else GRAY_L;pygame.draw.rect(s.screen,c,r,2);t=s.font_m.render("BACK",True,c);s.screen.blit(t,t.get_rect(center=r.center));return[(r,"BACK",True)]

 def draw_pause(s,mp):
  ov=pygame.Surface((W,H),pygame.SRCALPHA);ov.fill((0,0,0,180));s.screen.blit(ov,(0,0));t=s.font_l.render("PAUSED",True,WHITE);s.screen.blit(t,t.get_rect(center=(W//2,200)));btns=[]
  for y,txt in[(300,"RESUME"),(380,"QUIT TO MENU")]:r=pygame.Rect(W//2-150,y,300,60);hov=r.collidepoint(mp);c=WHITE if hov else GRAY_L;pygame.draw.rect(s.screen,c,r,2);t=s.font_m.render(txt,True,c);s.screen.blit(t,t.get_rect(center=r.center));btns.append((r,txt,True))
  return btns

 def draw_emote(s,mp):
  ov=pygame.Surface((W,H),pygame.SRCALPHA);ov.fill((0,0,0,150));s.screen.blit(ov,(0,0));btns=[]
  for x,e,t in[(W//2-90,":)","E1"),(W//2-20,":(","E2"),(W//2+50,">:(","E3")]:r=pygame.Rect(x,H//2-30,60,60);hov=r.collidepoint(mp);c=WHITE if hov else GRAY_L;pygame.draw.rect(s.screen,c,r,2);txt=s.font_m.render(e,True,c);s.screen.blit(txt,txt.get_rect(center=r.center));btns.append((r,t,True))
  return btns

 def draw_win(s,mp):
  s.screen.fill(BLACK);s.win_t+=1;alpha=min(255,s.win_t*4)
  t1=s.font_l.render("CONGRATULATIONS",True,GOLD);t2=s.font_m.render("YOU SURVIVED",True,WHITE)
  t1.set_alpha(alpha);t2.set_alpha(alpha)
  s.screen.blit(t1,t1.get_rect(center=(W//2,H//2-30)));s.screen.blit(t2,t2.get_rect(center=(W//2,H//2+30)))
  r=pygame.Rect(W//2-100,H//2+80,200,50);hov=r.collidepoint(mp);c=WHITE if hov else GRAY_L;pygame.draw.rect(s.screen,c,r,2);t=s.font_m.render("MENU",True,c);s.screen.blit(t,t.get_rect(center=r.center))
  return[(r,"MENU",True)]

 def draw_btns(s,mp):
  btns=[];defs={State.BET:[(W//2-150,80,"-",s.bet>1),(W//2-50,100,"DEAL",True),(W//2+70,80,"+",s.bet<min(s.lives,s.dealer.lives))],State.PLAYER:[(W//2-130,120,"HIT",True),(W//2+10,120,"STAND",True)],State.RESULT:[(W//2-75,150,"CONTINUE",True)],State.NEXT:[(W//2-100,200,"NEXT STAGE",True)],State.OVER:[(W//2-100,200,"MENU",True)],State.WIN:[(W//2-100,200,"MENU",True)]}
  if s.state in[State.BET,State.PLAYER,State.RESULT]:r=pygame.Rect(W-70,H-70,50,50);hov=r.collidepoint(mp);c=WHITE if hov else GRAY_L;pygame.draw.rect(s.screen,c,r,2);t=s.font_m.render(":)",True,c);s.screen.blit(t,t.get_rect(center=r.center));btns.append((r,"EMOTE",True))
  for ox,w,txt,en in defs.get(s.state,[]):r=pygame.Rect(ox,H-120,w,50);hov=r.collidepoint(mp)and en;c=WHITE if hov else GRAY_L if en else GRAY_M;pygame.draw.rect(s.screen,c,r,2);t=s.font_c.render(txt,True,c);s.screen.blit(t,t.get_rect(center=r.center));btns.append((r,txt,en))
  return btns

 def draw(s):
  s.screen.fill(BLACK);[pygame.draw.rect(s.screen,(i//5,)*3,(i*2,i*2,W-i*4,H-i*4),1)for i in range(50)]
  if s.flash>0:sf=pygame.Surface((W,H));sf.fill(WHITE);sf.set_alpha(int(s.flash*50));s.screen.blit(sf,(0,0))
  mp=pygame.mouse.get_pos()
  if s.state==State.MENU:s.btns=s.draw_menu(mp)
  elif s.state==State.HELP:s.btns=s.draw_help(mp)
  elif s.state==State.WIN:s.btns=s.draw_win(mp)
  elif s.state==State.DYING:s.draw_death();pygame.draw.line(s.screen,GRAY_M,(100,H//2+40),(W-100,H//2+40),3);s.draw_lives();s.draw_diff()
  else:
   s.draw_dealer();pygame.draw.line(s.screen,GRAY_M,(100,H//2+40),(W-100,H//2+40),3);[pygame.draw.line(s.screen,((50-i*10)//5,)*3,(100,H//2+40+i),(W-100,H//2+40+i),1)for i in range(5)];s.draw_lives();s.draw_diff();t=s.font_m.render(f"BET: {s.bet}",True,WHITE);s.screen.blit(t,t.get_rect(topright=(W-50,80)))
   if s.dealer.hand.cards:s.draw_hand(s.dealer.hand,280,s.state in[State.RESULT,State.OVER,State.WIN,State.DEALER,State.NEXT])
   if s.player.cards:s.draw_hand(s.player,H//2+80)
   if s.msg and s.msg_t>0:t=s.font_l.render(s.msg,True,WHITE);t.set_alpha(min(255,s.msg_t*10));shk=int(s.shake);s.screen.blit(t,t.get_rect(center=(W//2+(random.randint(-shk,shk)if shk else 0),H//2+60+(random.randint(-shk,shk)if shk else 0))))
   if s.state==State.BET and not s.player.cards and s.title_a>0:tt=s.font_h.render("DEAD HANDS",True,WHITE);tt.set_alpha(int(s.title_a));s.screen.blit(tt,tt.get_rect(center=(W//2,H//2+30)))
   s.btns=s.draw_btns(mp)
   if s.state==State.PAUSE:s.btns=s.draw_pause(mp)
   if s.state==State.EMOTE:s.btns=s.draw_emote(mp)
  if s.cheat and s.deck.cards and s.state not in[State.MENU,State.HELP]:s.screen.blit(s.font_c.render(f"NEXT:{Card.RANKS[s.deck.cards[-1].rank]}",True,GRAY_M),(W-170,H-55))
  pygame.display.flip()

 # Input handling
 def click(s,p):
  for r,txt,en in s.btns:
   if not en or not r.collidepoint(p):continue
   if txt=="NEW GAME":s.new_game()
   elif txt=="CONTINUE":s.clear();s.state=State.BET;s.bet=min(s.bet,s.lives,s.dealer.lives);s.msg=""
   elif txt=="HELP":s.prev=s.state;s.state=State.HELP
   elif txt=="BACK":s.state=s.prev
   elif txt=="QUIT":s.running=False
   elif txt=="MENU":s.state=State.MENU;s.player.clear();s.msg=""
   elif txt=="RESUME":s.state=s.prev
   elif txt=="QUIT TO MENU":s.state=State.MENU;s.player.clear();s.msg=""
   elif txt=="EMOTE":s.prev=s.state;s.state=State.EMOTE
   elif txt=="E1":s.react,s.react_t=1,60;s.state=s.prev
   elif txt=="E2":s.react,s.react_t=2,60;s.state=s.prev
   elif txt=="E3":s.react,s.react_t=3,60;s.state=s.prev
   elif txt=="-":s.bet=max(1,s.bet-1)
   elif txt=="+":s.bet=min(s.lives,s.dealer.lives,s.bet+1)
   elif txt=="DEAL":s.clear();asyncio.run_coroutine_threadsafe(s.deal(),s.loop)
   elif txt=="HIT":asyncio.run_coroutine_threadsafe(s.hit(),s.loop)
   elif txt=="STAND":asyncio.run_coroutine_threadsafe(s.dealer_turn(),s.loop)
   elif txt=="CONTINUE":s.clear();s.state=State.BET;s.bet=min(s.bet,s.lives,s.dealer.lives);s.msg=""
   elif txt=="NEXT STAGE":s.clear();s.state=State.BET;s.bet=min(s.bet,s.lives,s.dealer.lives);s.title_a=0;s.msg=""
   break

 def key(s,k):
  if k==pygame.K_ESCAPE:
   if s.state==State.HELP:s.state=s.prev
   elif s.state==State.PAUSE:s.state=s.prev
   elif s.state==State.EMOTE:s.state=s.prev
   elif s.state==State.MENU:s.running=False
   elif s.state in[State.BET,State.PLAYER,State.RESULT,State.NEXT]:s.prev=s.state;s.state=State.PAUSE
  elif k==pygame.K_h and s.state==State.PLAYER:asyncio.run_coroutine_threadsafe(s.hit(),s.loop)
  elif k==pygame.K_s and s.state==State.PLAYER:asyncio.run_coroutine_threadsafe(s.dealer_turn(),s.loop)
  elif k==pygame.K_SPACE:
   if s.state==State.BET:s.clear();asyncio.run_coroutine_threadsafe(s.deal(),s.loop)
   elif s.state in[State.RESULT,State.NEXT]:s.clear();s.state=State.BET;s.bet=min(s.bet,s.lives,s.dealer.lives);s.msg=""
  # If the game is a little too hard for you :)
  s.konami.append(k);s.konami=s.konami[-10:]
  if s.konami==[pygame.K_UP,pygame.K_UP,pygame.K_DOWN,pygame.K_DOWN,pygame.K_LEFT,pygame.K_RIGHT,pygame.K_LEFT,pygame.K_RIGHT,pygame.K_b,pygame.K_a]:s.cheat=not s.cheat;s.show_msg("CHEAT ON"if s.cheat else"CHEAT OFF",0)

 def update(s):
  s.time+=1/30;s.shake*=0.9 if s.shake>0 else 1;s.flash-=0.3 if s.flash>0 else 0;s.msg_t-=1 if s.msg_t>0 else 0;s.react_t-=1 if s.react_t>0 else 0;s.title_a=max(0,s.title_a-1.25)if s.title_a>0 and s.state not in[State.MENU,State.BET,State.HELP]else s.title_a
  if s.dealer:
   s.dealer.blink_t+=1
   if s.dealer.blink_t>random.randint(120,300):s.dealer.blinking=True;s.dealer.blink_t=0
   elif s.dealer.blinking and s.dealer.blink_t>10:s.dealer.blinking=False

 def run(s):
  while s.running:
   for event in pygame.event.get():
    if event.type==pygame.QUIT:s.running=False
    elif event.type==pygame.MOUSEBUTTONDOWN and event.button==1:s.click(event.pos)
    elif event.type==pygame.KEYDOWN:s.key(event.key)
   s.update();s.draw();s.clock.tick(30)
  s.loop.call_soon_threadsafe(s.loop.stop);pygame.quit()

if __name__=="__main__":Game().run()
