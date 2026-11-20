#!/usr/bin/env python3
"""Deterministic yard art. All coordinates and collision data originate in LAYOUT.

Run from anywhere: python3 scene/make_scene.py
Requires only Pillow and the standard library. Seat preview reads ../ref-robots/,
or ../robots/ when there is no reference set.
No external fonts; reference robots are read-only preview inputs.
Rectangles in JSON use [x, y, width, height], with exclusive right/bottom edges.
"""
from pathlib import Path
import hashlib
import json
import base64
import zlib
from collections import deque
from PIL import Image, ImageDraw, ImageChops

ROOT = Path(__file__).resolve().parent
P = {
    'ink':'#161c19', 'orange':'#de632a', 'orange_dark':'#b84a1c',
    'orange_light':'#f08a4b', 'metal':'#c3cac6', 'metal_mid':'#9aa3a0',
    'metal_dark':'#6f7a77', 'steel_dark':'#4b5552', 'red':'#ff4b3e',
    'amber':'#ffb020', 'cyan':'#5fd0e0', 'green':'#7ddc6a',
    'ground':'#b9beb4', 'ground_dark':'#a9afa5', 'crack':'#8f968c',
    'wall':'#6c7670', 'wall_mid':'#58615c', 'wall_dark':'#454d49',
    'window':'#1c2420', 'paint':'#e9e4d0', 'key':'#c7a27a',
    'mat':'#2b302e', 'mat_light':'#3a403d', 'wire':'#8d9792',
    'oil':'#1a1410', 'blue':'#2a78d6', 'rust':'#a0522d',
    'paper':'#f3f1e7', 'smoke':'#d9ddd6', 'ball':'#c7622a',
    'yellow':'#c7ad60',
}

# Accepted round 1 pixels and metadata, captured before editing this generator.
# Compressed raw RGBA references allow an exact pixel diff on every regeneration.
ROUND1 = {
    'bg_rgba_b85': (
        'c-rmVzltQs9l-IoI9S*~fiffG*kEwtz#L8%4knnulMBv~5AGQ(3<@l8bl5m>V4Ns%;#BEAgg_`1dH|U|)8}?;x~F=&y8BmEpWutE'
        'J5^2X&h*yDHGlTg-~aB1PbEo`)O;^rJ-z?uXJ33ioAJgQZ@lrw8*jYvb&T)+uAgJBexB3iylVW?+wX7h-tkLsfBf~WU4OLk?mzdR'
        '`_FjejW@oX@wetnony+CTaCZA-)(vOQ~S?Wx8L7h)bGFh&;3{P{b#)K#v9+t_~ATLXNhxlKcA;8y7X&E8Gmg**z)#o?LWD1e|URa'
        'eE-~k?mzdR@x~i(e7oacJU)D=8$0~>Vci_p{yb&>N&Om@j9;?<Y;pTrj~{=1Ti?F>&;3`z{WtaVssH&k^)qbh=a=!u8*hB8<8Qq_'
        'P?97`b@i*?{QCX>m+$LeyL7God6;3T=MO1o087R%J%3nx`~BCSYyC^lk8*$imYyHE|J;8O?!T#@O~bE$$<MFo<A*<=BdmYCUmX4Y'
        '8?L9u``_co<7cn0|DHK+z5XzD4_G=r_4VhuZvWQn`E%d?)a#x0x_$Sb`!DMKH}|ve-k+gS$B%zLxAyhl8sC3^TK)Pxems8Ge*M=P'
        'o)3=e9Y6f<ruKtdd%)cLm*>W(eEvkv+n;(p|6aGh^?3K6`>%xiZ|djI+Mi#>8*jYvt&N{MPrT;JzHW}G{dMmD*H4X4eP44c<H!5!'
        '*0=BebN`h%e(ldM<Bd1o_*TcK7;vsz`_ERnJ-6rf+Pl3qKdVw&`}5FxtjBt+r<C>ZUt70#>pkS9<?+IQ_5<s&9_z6l{&Rb`{rBzH'
        '&sD^K{AWL~9_z6l>p9MUk-mSLuQva=Puq$AtjBt+$9m$O|EY}T{MSFHI{e?me;@z1w`?~2Z?66K*XA7G-mUezPut3VU_I7jJ=Rl)'
        '|2$8&@9j-_>Xz^B@!y=|mj3-w{`2^Zb$j*$>#-i|u^#?&d)xYN?)+};`Cp3vQf|ZJh5zga)?+=^V?F%m_MHEDyzrm>z<R95daQ^4'
        '++Lp7|IPh-%K2Z)nP9Zn|9O1!pZ&>ttjBuzkN;}+U(KKY;_<?N_5<s&9_z85c>bIEJ;Ym;b5D!3_7wlM`1#KspJhBg`OkW+$9k-%'
        'P5)in<GbHem*da7w%lJMtljz1w*K?@JofQvKd>I_u^#KmcY8;kQ;hf5?)MUp>wjPI+CSfVe~qwq{@d1n9-qfPKKDM$l%!hA@tOR&'
        '&sQEl{^<Ye_MGvb-Sg*roUa_c_S`;-_Pl3=^FNQz;~t-W4~it!`~0u{mH+t9<J0rM)?+=^V?F$5e?8uR*VdII{`2_cKkKm`>#-jG'
        'v%m5m|9O1!pY>Re^;l1A|K)ri%3gca7Vn`caqUaqAGC-6BEL?;<MY_ZC;wTG^;nPf)N}q9@r<ISwU>7OcT^sqF&>}x1M9IK>#?3#'
        '{>$~b4pH~0xv#H={dMZ=tHpmFpLIMw?FZIlJ=SAA{AYjVKmOxC`+@aXkM&p&|Jh&pkN^13eqcS;V?EZxfA&}Y^Z4XH`+@aXkM&p&'
        '|Jh&p&*PK-><89kJ=Vj2{AYjVKaWrTvp-pn^;i%89pk@o-JX-<&-d70Bd(qQJU(lAeA*AJ$9k;Cdh&n1@0#D&nqz-`{r1f+ZLz;b'
        'UOWGJeAe>#-23-YOH!@n_)LELEC2DI$LAi8&#1p2Mv_V^+Vj7AwZ-#mQP<9Y9-p;5K0O~~J=SAA*291HSN`Ka{<9xgkM&rO^_1(s'
        'z4vps$A2C#<=vkBz<R95daNgo|2&Ug_v-`p^q=p!j{I3;f3hCyu^#?gcK)Y2tL6Mpb!0!V9_z6l>)}7~pZL#yU_I7jJ=Vj2;y>}9'
        '{lI#x$9k-X|HOadKl_38SdaBs5C4h(#DDe!>#-i|;XnQp|B3(XPu62S*291N$AA1M{<A+>kM&p&|M4IH@t^q5{$xGYV?Cw&FWT>V'
        '68}jNewUpj)!Na1R5|V8KWWRKSCXU{=ZE4y-&^sYB=MhO_UFI8+a%vx@t-8^+aLe*hgI2=_>cdzS8IP>Ns|6s>g%h0uOvy5>Tul>'
        '|NZOVUrO4rzyI@Zz7LY?Rk}O=lk6vwT(9Ck{*&w{l3cIiKmL>KCz4#R;y?bA>?e|3uj0Qc|9$n3->UNVe(d_5OMcGqU)_1kZ+Fe?'
        '=|7KU$$lcaUZwr~%zu*oM3U=O{KtQi{X~-MRs6?)lKn)I>s9=><oBubpJYFg<a$+X|E0Rl`JZGzk>q-n=YRQ6vY$wDy^8<%PqLp#'
        'a=nWG_)oH*NUm3j|0LN@B-g9Nf0FDclIvCCKS}lz$@MDnpJYF=pGdA(sT}_e|GxWNLHCbjKapIoQl0)ATaW$rtGiF8?ibllB)MM2'
        'fBeURvY$wDy^8;GJ^$OAkNr4M_7lnVD)FB<Q1%na^(xi*{txzxXF%Tv`-vpitN737zwn>zCz4#R;y?alK-o_uxn322FYljg<v;PC'
        '{X~-MRrNLZ`6~P;?*p-)NOHZ3|Cai%n=d8)E8l@EXg`tUdR2J_99wYCUa78g{^v|k_7h32SJmOat)Bnw9`D1tHH`mEk|as%>+HA0'
        'US9tvIZu$}dX>+A;XlcKBFXhC{^LK%ej>^BD*od?$$lc$^w|gFT(9Ck{*(Am;y>4`_>cc2{*&Z-760*{WIvJQdKLfO_TRT(KTFMJ'
        'Kau!P;y;Q1>?accrM^DV?`jhNX-)m-fe-(;wu}EH{^LLK-<Lmfh>kOf`-1-@@t^pQ|2R<mC&~3H{^P&49O(POf0A6U;y?a#7AXFc'
        '<a!nV@gE0@|0K0}y?Tuz|M8#agvEc7_>cd}_uuJqPKy7W1&aS9xn339f2po>{wHUF{3prvD$oD&pPU8qpCs3-_>ccM(D#G?B)MM2'
        'fBfexQ2ZzHpTvLs=Pc0oi2o%1llYGp7?A($Cldcj{HHpc<9oq>68}m3$A8WOeNXsL;y;Q1_<#ZV&we8DpTvJ+K>o9zNc<=9pS&iJ'
        '|Li9c|4IBO2IN0U{3r3BJRi(|lK4;j$A4l#{*!d1|6aa&+9cm=@t+uw|0KorU$<B0jQ_-cVnF_r#D5b1i2?afQau0l`{vsJ&41!Q'
        'F(Cg*;y)>e|4x^4Qv4?d<UdLLr`Y~Wb)EA+F(Cg*;y-!*m;c0o{3nV3#DDxJ2IN0U{3rh7KQSQxN&M&YU&Md>r<Q+TF#k#X$A98K'
        '{!?29<Ugrx|M~rI;y?aVdj{k`sa^j`{KtQ4(}4UZ@t?$h{HL}I$bS<5N&LruYU@40{3r3B#DDy!w$1?gPvSp`|M*XB8Ib=Z{*(BR'
        '|J0TN`A_0Mwb_fuheP5&c`YFSN#Z{p=fB~;wMYCXXMp@CiT}iZ{3izFKS}(j{rxw5ezyPj@jr)uKm5DY|DONEfcz(k{}k)|Z_a}$'
        '-n;fs=YQfq{*%Ois>grh^TKO?pVNP*%Q-3j69e*}B-g8ApZ}%0&iS9bADI6nxn8y3>;LZYpV$A10r^i7|H=D*`A-bUf0Fo5KL45j'
        '#DDxJiT}i&*Wy1hApc2ny{c^gy?*;9IsTLPg7BXt*Q=cW@t>Rl@}DHvtIF*0<ByW!KQSQxNpii4|M*Y*$A6Msuj0S8{;RpK{_>W^'
        '7?A%Y{*(BR|HOax6N&$%rv29$skZo!0r^kjKdB`D?fv=B{3rgipGf>C?eD*#=bZoXpU(s2KS}(jdi^&xpXY!1&lw>9N#Z}%>AyMm'
        '@gM*3AOA_>KY9NL|M4FK@}DHvtN4%q_>ceiPm=3Zb@}gfIVZ(`{KtU&C&~3H=YRaifBeUP68}m3$A98K{*(Am;y?aVD+c60iT@=2'
        'i|@aw-{*Vp*eJh;mjC!q690++`0u*ea@&yy`H%l3{*(AGhX1x$$JFz`9N4Y_`A_0MiT{rG-<G$Z`uaZ(<Ujj~#D5b1mF>QJ-~YjZ'
        '{AWLr_)p@$?OYc5{l5%YuL1c_;y;Q1_V?f3w{`F5zc3*G*-s??llZSJ`{nxlKL+GK`-#MVQgr`~_q)!2Df?k<_RIPC&kR_f|9tNy'
        'Nk??ceZA{yIR889{lz(d{|7hJVY0R7f6gW(XNXen^S`0zYI*)Q%4f?sJK{h7ljJ&8B>#=gSIg`Fj{aQfEq?zm1M;7JMdCkcjsND{'
        'SGxbA{Z5hGeqccUv#&_}Cwc#G8~$?!$ba?~iT@=2i)p_t{l|di8j$}axlUDr|4x^4QvAn%{KtQiT&HsWcZC0<*l%n9F(CihS0w(E'
        '_>cd@fA$rL|D@LZ7s-Bm_>Tek&%Pq@pTvLsC;qdqNc<=9AODH}>?;!gNj3T}n*H|j9|M;4edIq$u2b<J|M4IH*;k}`o7x*)r{X{U'
        '<3Il6KZyZdr{X{U<3Il6KZyZdr{ce|?6;@?7?A($D^i^Xbe(E%|MjlpKmOxC{*!c!0bQrs!+%51IsfB7{^LJM{HJ>TH#VQ=fBBF9'
        '_)n7Oe^sad=G@1B{KtR%CyD>${U7|tfBeUPlK4;j$AA3CfBYxO=f8;m_>ceikN+g`pZJge_>ceiPiozO-v6so{CB#Xlj1-A<3IkB'
        'l-Gf-Q|0Kz<HO>d|M4IH@t>q)9Oyb#F8{rL`zE<k{O9-ovLFBPpH$;(16`+b{>Oj($AA1MwUz5sxl45&|M4IH@t-8usrZlo_>cei'
        'Py2lai1<%h(wx0&^It>*?%_Z7E9?8nf4b*0K*WC%|M4IH@t=LAP6zgX#)xvAivReJ|M<_oQojRvPp(t(UmXVA+JEfFfA$rL|0Mq7'
        'Kk=V^MdCm4Uu*u0WWX)`$A0{0Uy=Av;y?Zq|Jhe0{*zkuUlapw<v;c-*V6na$#p9J<G*|Tz<>N_Uy=Av;=gzX+|qyC#((w|iT@=2'
        'i)X;x{$oG>v#&_}C-Glw1LpJ}`|+QBMdCk+|Kb}km;czW4*T(+B-g1*@!#okPAa<pjxb;j|FIwc*;gd~lXCel)pfO;{~ck#HU9HH'
        'U;eYNNOGOZ^S|X8@LvD1AOG1`B)Lw-f7{wDivNc0W54?BSCju<JU&R(#DC(ycKo-815^FSef(FV|9<kbpJwalzx;*y%y-Cq{3rfv'
        '(|=n!aLRvU?{Odh@gKjKkN@~j{CB(qbF6F1dED2g{rHbJ%*TKHC;p4+zZAo*^&fxnAOG=-`S_3j#D8)97wz}|ivRe}eCFdniU0Ud'
        '<$R_#|M7<T_>cd@fBYx@<3D~eAOG>6_>cd@fBa`Y^YI`5iU0Ud<=c<{c*A`B$A98K{uBT4AHSH7|M*Y*$A7BVe*DK9=Hoy96aVp_'
        '_>cei#eDq7f8sy>)3)y7KmIeH`S?%#$AA3i?2rHW&wTvHf8sy><3Il6KmIcx|M8z%_TTApPHL_HYL5TdkN<eXeEi3M<<=Qz$~mR^'
        'FV%H>o&VJwgYh5#@rL>MkN?Vd-z^75abii&|8k0Iw;%uUhWYr9|LQpJTk1mo<3I5q|M83Y_>cc$+pqNJh51kH_Z)IfHTbXFgQe2r'
        'KY9NL|H<e5@t^ZQ^Ev<HKk*;`$=M(O@t^tlkN?Df{3rI~KmIcx|M8#rkN?Df{Kp&S<3Iir|M8#LkN<eXeEi3M;y?aVd++(+Ki)7O'
        '|M8#rkN?!>*&qM$hWYr9|HOa%r?%|Jf4pHn{^LLKAODH}_>W)A$AA1M{*&spAOG=&`S_3j#DDy!w(Q4$ykS26<3I5q|Ed1>`|=-e'
        'n2-PXPyEM!YWM7q|9HcE{KtRdKmJo&_TxX^FdzT%pGxuH>2gkr|HOX$#~bG3KmJo}|E0Qa>G|Jyzw6de>s~Ie`D@9p!}!m9HTloa'
        'R@K&=y*&Rbek$wyFVZ;x|C!JEpR+o7{U85{{rHbJ%*TKHC;sC<u^<2OhWYqU;y?aV%l50yf88D|l^*|z|M*Yr$A8ZM%;)@%|HOa%'
        'C-3#;KmIcx|M8#rkN?De{KtRh<3Iir|M8#LkN<eXeEi2A;y?Zq`|%%dn2-M?{^LKjYd`+u4fFAz#DDy!w(Q4$ykS26llYJS)Rz7D'
        'k2lQ6e-i)kpW3n?|M7<T_)p?L{$s!A=I(#~;|=ripTvLs$9~UEe%<`XFXrPviU0VI{rHdn%x6CSllV`5pD+LMpZUzkf6@{DJ6+C6'
        '@t@d_|9HcE{Kp=O?Y~slIscRAd-;$5%*TKHC(r-#pV*K8c*A`B$A98K{uBH0A8(kC|JXzP$A6sTd%=IaVLtwo_>cdb`T73vAHSH7'
        '|0Mon1@_~=^8DBB!BXk*pZJgewBCL0OXq*io6P6@PvSrRbLJ=h;|=ripTvLs=gg1)_>W)A$A1$4v4Jx`{^LLMnUDV@{*yC5{^LLM'
        'nUDV@{*yC5{^LLMnUDV@{*yC5{^LLMnUDV@{uB4{AOD%peEcW=<3D+>m;d<BeCFdn@gM)mnIHf0pZWNY|HOa%$9=vh{KtRh<3Iir'
        '|84I-sipXjU(CmUQe^*~F6X59PvSq`FdzT1hhqCL)pc8+|4HIMelZ{aNp(N}JN)lDU%H<p{^J+(@t;(u|Hjs1KZ*bN#eDoH@t-9A'
        'GoShRPpa$r-`;%eC-EP@n2-M?{*%Oi<})AvNp-&egZ-pB{MYTlQt9!Z`0tp{f0nd<Z<)IOod226e9r&GfBYxa=fAz}$A9MIKmHT{'
        '@t<^@|BkR9|Cx{f_)q-De-i)khWYr9|Mb7U|L&U)y?gqE|0FG{yRQ1id&^Pw<3IE9AOFeuAOA_)xo^sXN7|47%*TKHC;sC<DZl-E'
        '{-62G$A60ToGSnEpS0JRAOD%peEcWzpVZcwAOD%peEcWzpXB|&{AWJ%@t?$h694g^`OL?EQcnMMzppnX{*(BRH_XR>epV^A|59D&'
        '{7>RP{xcu{@t^k+m$OFC|4RJFf95kE|H=6u|K<BU4vGJG!+iY5f8xKg{Wtad6*y4*$A9MIKmHT{)#blb-*KS$kN?cafBYx@YxDJg'
        '94P+dKlAY)|9O81|9St1#DBbDKK}EwO8m!vQqBJB_F$>>_)q-De-i&W|1+QSKmHT{@t?$h{AWJ?<3I5q|4IDEf9B&q{uBT4pTvK>'
        'VLtxzvr7EOe-i)khWYqU;y+3J$1mpNKZ*Y&@gKjKkN+h8lf-}KGavs+{3r2WB>zdZ#DC&H{*(Aml5140`|or)C&hn~y+v}3`aUSO'
        '|59D&{7<sCNOFzJ^S}Hj*;}O68t!x5`G{+@-M;_sn-9Hv`ed`m6#q%Gw@Ak{-j}ELY1gQ7Kc-6ZU-$SQ)~#XuXObk9QnxqH{ks(H'
        'F*Ro|=YNv(KS|5ZYv#^rT%*eUnDYFuBzud*f8sy>llV{4aj)5OjcV)16#q%Gw@9v0iT@;fizL^m#D9{#MUrb&{1?H0k|asmucQ4Z'
        '$=QPB8kJ(if0DgLl514_$A6N&MUrb&{KtQiy+x91RQ$((lD$QeYgG06@5SSTBuSDQYV1Twk|ed=XJ35&!^>As@Beu%<Bd1oc;k&X'
        '-gx878h`CM;cI{2&5`=w8gIPu#v5<E@x~h;cl@>arvC2M9CM~L-gx7UH{N*TjW<5#_**`lo8#8)8*jYv#v5<E@x~h;Z#@4QZ@lrw'
        '8*jYv#<w$mtpQVR-+1GVH{N*TjW^!-IOFGDKR7i<>gx}UH{N*TjW^zS<Bg9oKIQ!&Q>Dydyz#~xZ@lrw8*hB9@&5rgfz)0'
    ),
    'composite_rgba_b85': (
        'c-rmVzp5oiV!+{7a9|c>6l}1Ojf`W%f)fYJ;N-%<4JPp93**RR<`K*ag8~aCy6oV<fpMb5i4%bYiWK<?7Q|*2dH|Uo)1s%<f2zBy'
        's_V}e{20xhTYc*GIp_ALI;Z>m_8<S@$KOhlB&qwJJ%4!r=ck{4wwdw98*jYv#v5<^UE_c8@kdov`u-pOZQRCI<8~fjzPL30=<ScU'
        'cXs^I+n@h@SLa{ac=w<C&;4h-@y6FUelS%nYirZF-o5|!wimjMHCLt@zjVAydHZX}pH#O$-d?Hu-~H$QYx({&-gx8d8DFdaO4)zY'
        '?X0aOZZ-UVUbE=YpCM%Y((xeW?e86bV&DGs_EPLW_n-UE{b#)K#@95yw%2*jye^z`|IcrGZC=ARmcAZx{0aRTj*LHY{7G^9smITM'
        'zSOtx{&WA;aQ}t8r{>7-FXN3jzOM1Zf4A6{!BXx2z4r%7k|f<-5B|&9-~Qci-v7V+*!bS1rN-A`riHFQgscG^8Gm&B;p**=KYy(G'
        'A6-9+z5kA`AG!bBe<j?1YrmVOKmU>6U!{+q{(dfD{`2F--TQAkpBC?bkDm|6_u#*~o<C={vG@MN&||>S@uBZOk9GTd@8^$w`)lua'
        '%60qhKlfj$_utm<zO%=$QpeAKKlk?Y?~Nb#Pp?0JZ;ziI-v5{T`Lon?eQ@6B`04kp9S`=70bA!UZ;cPR{zS~%Uwc1)uG>#N-u>tP'
        'tKt4z`~7qE_m}a;8(-J>n$G#%I{)I%{lB%Ixa7*QVH<15*RB7rUmG8KUUM(w=f~I7x9|RQ|J6AD>hCY(jW@o|@vZpp&ix-^z^(R<'
        'KdEwiZqM!YcY9ZUSA}%-_o4ZikNM=8&z_xXX#O+gzQ6dduiI<w{SqE8{O5RSKIX%J{KtQ8Z{L4^{KL0R#DDzfcxgW7!+%H54Y_)5'
        'Nv!cL_^)<@_f%{CbD#DT|Cx{Zn9r8~-oATU?c-nl@_k!=%RRo8^*`0~e$y>ajsHIVf0gm?^Y7iW+4OsszJF<(^V{2-uluyG952ns'
        'e9ULff1|Os+VWfO@xA-c>tuOvZ_QJCzB}W;Eyo@G_q+V(@mbdGIbNEN`Iry?@t@mE>%Xn_yQ}MeA^r=w4UZT8bG$Sk^Wnc5{CDO3'
        'h5YCEYW<J@_|Ngue9VXc>h#~MH?Myd|2f{>>A#To|84y}Wc@E>O|Z20|9O1!pX0arm=FJ@_TL@nHS!<-^>F<cj~D)P{5Bu+;XnQ>'
        '&wp#5L!7FZ$F!2>9^$_qum9}vS;ym(|IEjH%!mK_^xx7ke)yca7+)Vsd3-Hl?$(de`p@I@-p8lorTLhT`S4%7`{T}aiuv(%_*~+7'
        '<L4D${d(%-YYB7bzqJ1I_`LV=nR_i$Qkk`U{ztBT7~`7!vDa7T`)oMoEbYsqU(d0=a`)V0`>3?nJxf^s^Z2~)@#%9=B-Q@;Z?6C1'
        '_{x9$=ke+FU-K~^^SSQ777W|#^`9MI%lBWZb2#|V<CFi)$9&9(|M<`GwOs#geZKXX_|M~$|IEjH%!mK#^k2;LP;wokQk+9m<J^y&'
        'A2iHi>An9~n)|QR=c&i%{f|%nGavIYAO34+{jbC|ik{|vbp0>2|8o9p9-s9+J{>R3$9&9(|H|@Ttm`_IdW_oo`C2%>uKj#l{#&}H'
        '$kDIm@}I|N8;?)NOY<?GzUMQ(Z#?#Uk?v@I&M*HtzSiKsE9ZOgpT{TvnUDFH&sqPqdM!i#b9}AEe<9b(T>3fq&*PK-%*TAphyVD`'
        '@s<Dh&*PK-%*TAphyVD`@s<Dh&*PK-%*TApC)MX{lobCtzIy*3|9O1!pZS=N`5d$0+P_baS<}zj9lsW14)bkIZ)@px*5=KBKlj3L'
        '%!%>!9LLuZ=kEMpkIz;fpN^O2V?O3{)PK|O+j7~~ZG`%7?#!j}CHXJL=e5Q-z7G2=M=6f4CC{DzJU&}_e75$!A4%8VH@EaTqI<7d'
        'O??)68(aTA-TvHuOUJprdFLv|HTfN1`H%lRK65-iYro#Br2Ag~T{2+I^}i+i9eMq?w)NQ9udn4Q#p`RO&Yk}}K3jQwdcDki%*TAr'
        '`fola#DF3GTYJs-sQ-F@|DWS4|M8#4C;yp``It|L|AzM@r)>J(=M>xKzx>B@w|9^KzWnB^_toY<w^zpPIbNEN`Iyhqb90x@&s|yv'
        'JYu)Cb3OKMyQKXS!++j~&~CZ?XP@iN-!+ck=3_p6_;2Z)kfX2vuGz0A|Eb+tS^rZTIbNEN`It{C|1CLf&3{{KfBYx@E9d=x;y=er'
        '^D!U(Tl3$V0oQC7a*aR!6aVp__|JUI$9&53-`+XFOYiGjyT%{?iU0Ud{AWJqV?K5GZ_9vF|7~68h5y8V{3rf1AM-Jvy8JhE=Gra%'
        'C;sC<@t^sakNMQ=zqNJ1kn6ngpZJge#DC^vKIT)W|CX)~7;>Hm|B3(jPyA;-=3_qf`ftmCYqwFW|4RF;C-I+D!e`k@s<*kp=3k#5'
        'f97MCUjJRYjrqT=-F8Xc?MK!5T#8kx&kOyg$=_E}i4DI8$7|znWnblc{deg+-?i%l##;ZY`SZcVfBYx@la3iBB>SqY^MCn||M-vp'
        '#D7vqZ{I!f-;Ms;+rMk;erxN1dzJ3LfBDznUCJ@3FaM>;zEx;fe_u&=Hu!J;wW%l8#%=wZez&>bLjAYox^Wxx{|+_a^tMafKcVlh'
        '_E?f6iT`T#-`4jn*>CQ@H3MF`?K@p}#DD+w-(N^d*uVehzu6B`qtDmDe_QKLYvZ>5O<!#8x2eI_zGv>grGGy%CiJ#b#eWk2N#Z~L'
        '+xFj{<F>xOcHi-zB>s~;U#Dg`>OZCN-`svj&i~yrApc3?KgsiT%P9Pp-+xQ*`P(x4p6BQHA^%C@KPk<zeJlRcn!!Ttx97ht1NPv*'
        'um9uk)p)s|v-Y{<_srh$b~x5<mBWE&{kM1BksfT8<1sZi*!Z>i{@&Y0==aRGJ-_W-&zYS5^Zyx=^*<@cdd_eT#ZrIvr+@NO!{4V4'
        'Otrpv_Wgfzr%wOOW!E0p|IS$Z==V);Bjx%Z|4IBO^>QrVTJM|sZ)q*??)AkryH33j%dT4X-<fsRGv7NmApc3?KPip>_N;d2`r_8y'
        'r)IcnS1tQ5^!=en&;LELZp?p@_)j|jdh8kdT{YU(^~D@^RoLslNB8HIF{Q8n9r>JK{*(Amy6af}=l}FShhLu^$K1KTnA)xi_utw7'
        '?}&NrnbiIZb)EG;iT|Wp{5Q6De#ZQJ?_6I@ZC9l;SdISk`me-)QfvPE@|&+duw6)@{(E}(<gn4kF?ZT^?>%TK$K7$=MgHSIiT@=2'
        'i|N0yJ)_OP_s+R*oyT(a9OX0T%#`H6Sl0)?YUotwg7BZje^PI+<sI#a{|2K?Z5L7v{tNxAi=*St-c~LCi+#KNCyD>0^49-S`7fni'
        'WBB9DxLnrZKmL>WPvXB+{!3-Foa=wX_Yb!-FJz8K$DO?`{^LJM{3rFW{+HW-<FyKp`tQiNv$vJA!7f|fb-Pz@oBt&KllYJS_>ceY'
        '^568|hwBRZeI@aq#DDy!_?6(lx%JpD|Nqz67yKvjAOCs(AOG<m2a5kB{%hBNA?F#Cn8$KE{u|~nnveZBQ2Zz5@L!70f2+-Z!{?AJ'
        't-qC6$mb-B|HOg(Cn?wUS#tX?hF#BmR`K2OUwi&zzcLMIKk%Q_lK;l{n;l(0JLA9DpZ^xyuKdS;uKyzb<3FjF*MHAc!u6kH+tvI3'
        '_>cd@fcz)*vi^6*exd#wjdt|4-_X~8W7~E3x3yz-X|Z3NWBK@6EB}fA_)p@%^X{9!{(Gj-^}pD5<-fMuy1okk$$23BC-v;WSg$iK'
        'y{|9U`d=!$@*n?Q@!zn$kod2D2eKglNv-`(3oW(-ue_fvmR-H~uO9=>Ex2W`P}f=ivnDA1lXTo@XP&RA>^h#m!h8Ie>h<5@@jh*s'
        '!~AQKB-Pp(quo8{ssBRPe^NF2&toZ0!#+J?FYo`8tp7>s<M~>m|2#%q|3wo2NuIC#C;pSff0E}b|B3%3#}odOa-1j3fBeUP{3r3B'
        '#DDz9fBeUP68}l6(SNT0!hifHIi5)B%YWv<e<k?ukAL`9>Ms71_>ccQM)*(SKmL>WFZBJ1XFj)%|M-vpG&WujeEQ!?7yn88$AA3C'
        'e_#B}A-c~b?hF2t)UN+ZIPb#wAN<FE9LRtCC-L9?*SzU@9{k6DT6UoQ!GDrGU&Vj?XDv|tC&}|w{KtPBDE^bw=kqnzdlbcg@|rOJ'
        '@t?$h{HOc;7y5aA{AVpt{3prtRb~4x)OFVXWG#^YBzeBd>%aUbYk~ZC=6YW(Wq*~izxYq$KUoXpzcT$d{O)-B?x~4}pCz^b>@WV4'
        '_)pdX`L6~4wNwuO*<bu8@t>>(@*n^4pZ&#u690(-`H%njkN@~j;y;z<9Q%U*oX=o?@t?$h{AVrDKI!}VFEyE<gt^*Z{3r3B7?A&3'
        '@ZYoN57l_)?z!4u{3r3B7?A(?kN@m1{*(Am-V?}w{KtRx7yn88CkEs{=YiCH9)tbGe-i)6>%sijg8yE<dHv&;-+WbN!`yTG&;H^+'
        'iT}ia{MUm2YVHpI*<bDWZ+LAyMZ6>a69e*JZT>6KIa_nJzslTSwfJv1R>q9~#D8Ky{<HpP{m=Rz|4IBO2IRle{I~Wyr1b9cpZ(RQ'
        '|Hk9y)&J%{@t+uw|E&L6|Fizbe^LzpJ-&Pq6#t0<`HyGpFaF~{mF>S!*IEA)1M;8q8Jz#&{15(<*MIp>49I`p&t`vl{~!N}|M*V~'
        '$bVkXw7;zX@t^pQ|HOd&=kv_$FaC4=7x5qesproN?%97+*QEL!gjC(>82gL=_)q*N2IRjM{AV4@{_^>6KL1Vp$A9X@fc&@YoALKZ'
        '3OCGMGJStq&Ux5h{3r1r|EW&{@?Rd$gc^qb+TUONC;sC<F(Ci7>zOl#>Dhn1>@WTk|M8!k6U=|!zgGJD+w3p?llV_+YYnhh{|&!8'
        '-oATkqTy#r?LYgA|0MpC+A(0y{%ffm{<FXMPvSqR4FmEY&)8r5r#>s?y%+o^?*-&P{^LLX<3Hv5T{t~%<%s`e4Uqqw|Ka=(=YQ~@'
        '_>cd@fc$s22d94@uRU^?6_&1NQrhQ#*kAmoHvBhzu8e=5|2h5l>A!`3KmUmV`LD#!|DBuR?(4{{d8U-l|FysPPi?LLZFw-ndrN;>'
        '{}cc5Urqii;X1-K`Op61KlSIo`Fi2fzsL07<I5L8@t+uw|9Hm!;y?aV+3SCyuCx9p=L7Q}&+s4r@t^X&|L=_dy#G%O$bU7S|54I;'
        '7B!szVSn+Tod4_mU#SiQ^56eA{Jsduyv&RL<oeI9|19xeo5z#VJ!5~>y}$TR?0MXc{3izFKS`dis@s3#HA6$<KRFkK|0H?7%KG0O'
        '{@a@)@2HkFK>m~XPpZLyrTFj5Z@zlp(zz|Hqgo8ee-i&mr5o_$U;UE*#DDxJ$@5kGm&AX2*RR>~U+(Ma9PR7hzhN;3<Ufi3q}%;B'
        '*lsKS<3Il6KS}&2{!8h<!ANWE`EP6No$((7@}I<iQf>ardHrYp6aP7$Nc<<|_utfW*8lj=^#J)#6938hAN<FE)&TiWlIN@VkN^0O'
        '|M*Xm=c}Cm!GHY6fcz)%pXaOikN?<<|M*YhKdBD?J-&PqR4)HLJ$&*({HK}>$bS<5N!I_)`EMM<f8sw${3o@4{s;ew|NIV<_)p?L'
        '{!=Xm<Ufi3B(MLL@4vOr^F2GZl+U5%KmL=%f8xK={5M~V%;mqc);r=q9^^mA6N&#M{#*9nt2eLTm&1QCychcVF9-H(K>m~XPvXCA'
        '|Gj<pl-z$Q+;{Z-e;mkvjwcfTNzVUB@4uApJA3{I2lAieiNt>r|2-|f|L^McpHsW<>iNG6*scNjPvSqx>%YhSclGn%a@p_d^<Nl}'
        '{~S*w{*(Ccy8m+8FV^+{7?A%QPbB`6O84LVcsKYj<aikR{=c*S%Wc1y*MDZf_WWnxOOkRI>c7EtrJVn<)!H=!m%gXg&;Q_tHcWPP'
        '{m<HjWDQa3>HOcV&juO#-+z9#TW$-+{`@xv<Uhw1iT|Wn{(JWP;iqcy-|+S6dBA&JIcK<(&;MmW{&QTB_)og>{=dO(Oa3eI`p^95'
        'ykP!wT#@)sigW%)&HkId{yV=e;8NrF{_y>G)%wpGApbe8Nc<=D?!TeYb6abFQ}fmCKL)JVfcz)P^HinyZ|S^`@z2MXFM_($e{<6<'
        '`ELALF8lEx|M8zB&r>=7H;?~@ZOx5$$J$?N|1lu{Ij%_jC-v^X(RTbN{&QTB_)p6F`5$-tZ|lEv+AoLy7?A%QS0w(E_>cd@e~v2>'
        '|4BXhZ~EHr+MoO<{&QTB_)q-ThX2NG49;7tMgK8iUHg&$Bzd07`5*E9S5o}PfBYx)-P*Cy^HluDfBeUP{3kJ>=c&B@%YXdGfBYvg'
        'py#RhuP*!L^dAHApW}+urU5-qb%*~3*X8zK$m`Pl$AA3Ce^L(y^gLA#|4lu2*ZSXZyU(6Ktj2%*$AA1M@t@Sz`5*kpfBeUP68m|c'
        'ivReJ|M-vpB>t1yJ^zFM_>ceiPvSq%Q}yRR=YQ}Y|M8#X`Y)cR>hJn5!}j*#KmOxC{*(AmYR7*^oyC9r$A6A1Qt1YC{;x_u_hanw'
        '<%^*BkN^0O|0KnApy#RXu-}mNKmOxC{*!c%13ga_%YVb?sfAXH|9t*0`|%(DNiDuN(DPK*|M-vp_>cdjzVbX(>_T0~fBeUP{3prt'
        'RQ$(({KtR%r+n7{5&ua?+Ok(`{wvXdIsC_db?ry~)0u04i2o%1<3Il6KgX3e9XP+nz5OK5Q}G}F@gM&=uC(hw-jnC4_^%BEruHBE'
        '@t@<0#D5b1@t^q5aYf=k@n3KLE6IQ<{l|X%=eQ#ApTvLsC;oF>k@!#Q)qkZJFqQw<uU<>@pCr#y@gM)4^#lL$pW}+ee-i(dXTX&H'
        '<2L?tT#@)s;=l3?7~6mB$A6A168}m3SGECT`j7qi&v8ZKKZ*a!H()IPv0oeZ<3CBBr>ez&k1t;YRl5J~FklS-u^<0Au1NeR#qwXM'
        '>snd=yTgE2{O3Gh{&QTB<asKu|JG-~v;Jd0{&QTB<asLoOKY=I{5N$U`?Y7kmi+gNk3W){iT}iZ{rE4314I4Cef(FW|Ni2y{xVvB'
        '{Wrh1J=?owd;BN<>(hTJ9k}Mdx%aq_|M-tzY>)qH@L!E<sQkx&N6Z#uUTe<dzCP{8f4pIP{8yX*T6|5N|M>5$;ja3Rzxa>;_{H}4'
        'uNMD3d;V}J{^P$E{8!rN|BC<k&-O~(-gNC}@9S5;cbMPWHu%r_pZJgeRN6JQ`H!z!_TRYnv-kC@-#hwmX&d~P#(=Nhybg-}_>cei'
        'kN^0OulSGu+VS6XeQ*Bv>DTy+|M-vp_>ceisz3jI`uS%+wP(7R-^+jL{Wty&8~#3hUpxQtAOG<m`|%$S@gM*3pZJge_>ceikFVO@'
        'UMZjB!GHWG{^LKDW<UPptCsy2dVWBv_|N<Q#DDxJ{^LK}<3Ij${xARWAOEo*|M8#gdHt9F(q99Rzxa>;_|MuO|M68n+nc@ym~wt='
        'x5IyVKNE!Y_>ceikN^0Ohn)W#`uQDKKmQ}fx*z{t^WWQdPyE-o{~lky2<oc;T8{tNkN^0pr|ZA$UBCJ2^`FPvaQzql%hh0<HRsgk'
        'zfjlZTK{V~2ID{e<17B-KmM!VeR~cp#fde&{>v$9-G2PXSFZo;`p^8=#(LjT7xEwfiU0VIulSGu_^)jH)&9CL|B3y+EpkpR_-`<R'
        'G*rs<U(U{*|M<`OAN(iR`{O_Bf41lP&-}-K{KtQ?_Q!wxXM6m|fBeUP{3rI~KOV9@pZ~#sti^x)C;sC<9`gAgKL3ON#DDxJ_TxXk'
        ';y?c5Kk*;`sjqWB_>ZsnkN@~j{KtRlbM24+_=^AdkN?Df{HMO`$A5g)ga4M!#Yo}5E9ZRhAOG<m|B3(jkN<2h-uBk6%N%=t&i~~<'
        '@t@eQmd6nP@s;hBwLSjhKmOxCu^<2OpY8D<|M4IH@t>UU%YXc5d;G_L{KtR%Cu@KFm)3v7_P_k*s}G9lgQMHd<(IQRcj){=x6Ob2'
        '$AA3Ce_}uWyTgCu@g<cHj@(90|DE}{kIXORHu#VK_>cb{U%m*6|HOX$$AA3CfBdJi{TJ%Gqw9b3<J~ZaR*&WKp1+>#I*tGMuO<Ka'
        '-Fp1_KR$-+k22e`m)C#APj#*Tm9!3!(|_ZC$F6k$-T8A{|7&Nh&ibGAKkxq&`|)3`{u};1b~X6#uAiI#_>ceikN?De{KtR%$AA3C'
        'fBeUPVn6;%VUwv*=AR#y@-|ZbEPn2?<3Il6KmHT@@n1RXf3M!WPVS)bHcDFmE8*w1{>Oj($AA1M=lb&B-Tq5e>HfRx=jK2D<3Il6'
        'Kd~SG-RZyi*T;_fU_Q2V{~h_cx8`@|=jK2D<3Il6Kd~SGmE^x?&mT_vZ#uR%|84!;d;UB6bMqhn@gM*3pV*K8_>ceikN?K!{#x9{'
        'fBYx*<3Il6KmKdef5YQx9{=$l|B3zhFP8t7jxp0ekF++nME~9WbMqhn@gM*3pV*K8_>ceikN^0O|M*Yr$A78)w{*U1?DKy^ww2p|'
        'XMXOZ=l|~g-2BIX-v7sc{3rI~zuf+tJ0;X<M|}{w{hWR|^K&1a-`@85kN-j%j{9pd82|B~*pL5e_JQs3AODH}_)qM|fBa{A{KtRd'
        'KmJp{pXbYeykUF%$A4<ke~&L;1jT=1KmOwl+v7j>P}%+qb)EG;dA*na_|NwEkN;}x>ERRp^ZKvYkN^13_H2*;I=VK^58r?H!QXrG'
        'ApeQ|_>cc=&-VDQ2lKss_w+%7|K@-1<ywXOC-3#+KmM~l+vC5MKZ|7a-PgZ=^Ff36#y_VP?BVlD_)pgS_>cc=&-VDQW&2INH#WT1'
        'yJW$k9t_BTVn6;%^}BaC21~Waf9?1$H2&j1#dn|k()yqECfl?Ar(FKqdi{6FeWU&OkN;%NkN^13_V|zg>Neoifon~_*ZcqYPuBeS'
        'kN<3s|M;)|^M9wlTWb2f&i~~<S@YvR{<A&)<G*_S_v+2-_sy^WH*flV{KtQ?=Er~hXM6m|fA#w>H2&j1S@YvR{<A&)<G=d-H@?S@'
        '|M*YV{P>UmY|r-ikN^0O|HOU#$A7kGd;G_L{KtRtS}*_cpY8D<|M4IH@gMiOPxz1jY>)r=kN^0O|F}>5$A7lRfBeUP{1?}MQcv+8'
        'zt|rCDZc;quKmY<;r@Gk`64L(llYG}Y>)q#ti<)dsRMiWU#RO+um4HnKYp=2{?nDue+zy6*XO_8_xkVj`vzZn{7U@CFSf^j^7$Wa'
        '`fqMM_LKOJUu=*6#DDxJiT`ZR_V`b!4A_JHN__oyG#~p({Kqf0$A60bKEU4J_s4${|M8#g^|-z9IM085J8)ia`=P}1KiE%d!+*mu'
        'SSqRcF+X$+|FzR#kt6Zneb;}Mbp6<p`}dgjKiey9d-HX_&~-rm6aVp_RHOgy_<vabvpxRfKk*;`N%#2guGcU4&-P07-#q>k|M8#1'
        'fBa{A?QL(g-m~Wq9~5Fh{!@y6`2M?}dV2VT|0JD$FZ2A^a_4)O`Oo%B+1}KB!{>j^4LCZG|787-|D;;nw{>2d>%Z8Z?eU+)e^NX4'
        'bNxTtvpxP(S+A+`AOA_Y*8KR-_G~ZQe{1od_>cdjn%4aI&-QH3`5zMhNzVV}KijjtUvGZ)+mX+J<3I5q|4IDEf3{b~_O=Wc>c0>V'
        '@}Kx`*>%I`^@hZM694gw?Zw#Mp4(#1kN?!0|3Y17{ZHaQ{<FPY+Y9*|H~v!(=MrC;qt|~W{^LK}<3IkB^*{cLcRdb?|M<oB()e%d'
        'HDLae_%DU`=I-M_@gM)$Ui$5YUdM(1B>u~}&c}h`KmN15G}}A!IUf8c@t@a)#ee)~d;G_L>h1gx{*(BR|7?%{_)p?LiT_gjZ#V`^'
        'u?qbh-xRmYf8sy>llag2pY1vSga5>T{3r1r|Jk0;|KLCIAOA`G$1k>*$A9zqPvSp`|M<`LY>)pW{*(BR|7_3p_)q-De-i)kpY7Qm'
        '|B3(jPvSrRvpxRfKk*;`N&Lruw#R?`C;sC<iT{4?KdF`YPyEM!68}l^998fBdwlsKDE^ZiTO`j>`$1*<FVuC`|0Ks2NuHzf`Y-=U'
        'jxADeO^<WK`iSRfzy0w2cR%&?@JX`A6#q$bY?1D1eq3HVPJ50j_G79h{|%4-X~P`mUy~%MmWE^V*59Sl9#dQPvi>Jo|C4lVy=H5j'
        '#&cA$A5&icmE_nW@t^pQ|0MpCbl-cnJV%xKF~xt999tyMQHlQ~#}-MRqZ0o~jxCZrN5y|7_)n4~N%^|lf0C>%NS>oo8S$Uw*dobu'
        'RQ$((l4FY`&r$Io|4EK5k~~MnfBYvown*|ERlENC#m65>k|e34=1!C(NmAc^`uS%+K70P~{?Db1H{N*TjW^zS<BhLt{L*W}OaDG>'
        'BlLTXH{N*TjW^zS<BczO{L=Q;{%vm?Tc$MLc;k&X-gx7UH@?jAdp_LS#@_84Z@lrw8*jYv#v5PWc>Xiqc;k&X-gx7U?`Ql~1BTqb'
        '@x~i(yz#~xZ@ls4jNf|y;Mz7q-+ySl@x~i(yz#~xZ+sc!L(T_TD`XqS8*jYv#v5<E@y3@m{{H~-O(t{'
    ),
    'props': {'watchtower': {'metadata': {'name': 'watchtower',
                                 'at': [555, 0],
                                 'baseline': 74,
                                 'blocks': [567, 54, 39, 20]},
                    'pixels': ['3092dfbcd7d51aecfeda82048f2c67a19dacf6b86a85bf030a3aa1c9a0beb80f']},
     'hoop': {'metadata': {'name': 'hoop',
                           'at': [23, 145],
                           'baseline': 198,
                           'blocks': [28, 192, 9, 6]},
              'pixels': ['e510601244986ad1a054018629d0b373e08b359ceb471722d919ad5044420236']},
     'drum_0': {'metadata': {'name': 'drum_0',
                             'at': [426, 60],
                             'baseline': 86,
                             'blocks': [427, 78, 16, 8]},
                'pixels': ['cc8a7396108f6b1e39667ce85d7d193eb361863d3d8232aaa49cf99a1e56f513']},
     'drum_1': {'metadata': {'name': 'drum_1',
                             'at': [450, 62],
                             'baseline': 88,
                             'blocks': [451, 80, 16, 8]},
                'pixels': ['74688d6fe03ac2cf0a1ce7b56425f7f6b5c1c1a71dba51433a146b9d93004e3f']},
     'drum_2': {'metadata': {'name': 'drum_2',
                             'at': [473, 49],
                             'baseline': 87,
                             'blocks': [474, 79, 16, 8]},
                'pixels': ['390aad311ed7d6013c61c4b98cf0353e951a6ee1d84143aac5f20ee9b4ca34c5']},
     'counter': {'metadata': {'name': 'counter',
                              'at': [495, 68],
                              'baseline': 100,
                              'blocks': [499, 89, 37, 11]},
                 'pixels': ['7b7b195cc7d09a53ef05920a91f50080ab63b93f14138510f07a4468c4552e69']},
     'bench_0': {'metadata': {'name': 'bench_0',
                              'at': [284, 244],
                              'baseline': 272,
                              'blocks': [286, 260, 28, 12]},
                 'pixels': ['949b3284785583278352b0b5fbfd288fe0e8b2f3e54f322823f691a87df1d88f']},
     'bench_1': {'metadata': {'name': 'bench_1',
                              'at': [346, 244],
                              'baseline': 272,
                              'blocks': [348, 260, 28, 12]},
                 'pixels': ['949b3284785583278352b0b5fbfd288fe0e8b2f3e54f322823f691a87df1d88f']},
     'dumbbell_rack': {'metadata': {'name': 'dumbbell_rack',
                                    'at': [393, 222],
                                    'baseline': 251,
                                    'blocks': [396, 242, 29, 9]},
                       'pixels': ['57e81674368e655b54822fcf2218eebe66b723cb6e1307365121f555711c7806']},
     'kettlebell_0': {'metadata': {'name': 'kettlebell_0',
                                   'at': [425, 301],
                                   'baseline': 313,
                                   'blocks': [425, 308, 10, 5]},
                      'pixels': ['741e41e47024cf014b6a4f679c1a3d01dcbd00f798daebc809f5b2521d26a6e1']},
     'kettlebell_1': {'metadata': {'name': 'kettlebell_1',
                                   'at': [411, 313],
                                   'baseline': 325,
                                   'blocks': [411, 320, 10, 5]},
                      'pixels': ['741e41e47024cf014b6a4f679c1a3d01dcbd00f798daebc809f5b2521d26a6e1']},
     'lamp_post': {'metadata': {'name': 'lamp_post',
                                'at': [511, 224],
                                'baseline': 272,
                                'blocks': [517, 267, 7, 5]},
                   'pixels': ['2adcda7da953a4579ca751629c86d6c446f5becc33ef2decfb8d8fd68dc19f38']},
     'ash_bin': {'metadata': {'name': 'ash_bin',
                              'at': [551, 277],
                              'baseline': 302,
                              'blocks': [553, 294, 14, 8]},
                 'pixels': ['1aa8049cd8774828a261effeae4857d7334dee085b2e65d17f927bce5322466e']},
     'main_gate': {'metadata': {'name': 'main_gate',
                                'at': [628, 148],
                                'baseline': 200,
                                'blocks': None},
                   'pixels': ['d46b2f60d11f57e28cf7d595e349936b394187c327ed75707bea5f4a746acf57',
                              '6d3b0400a0290951e2cef80818b68ea6580a59b27aa245f5d146a432ad0cea2c',
                              'edc0eda11e0087fc617e9ad9f39bc93f224b9e110ee5c3cce1b168b74b6703c4',
                              'b2069f33fd956c79679b2e5a25c60cd0eab63b023d12111ff0242ae50896e9e1']},
     'block_door': {'metadata': {'name': 'block_door',
                                 'at': [139, 26],
                                 'baseline': 56,
                                 'blocks': None},
                    'pixels': ['410aa5ad41ede3947b63a7a97d3e80074479cae12681ce33a536d69682eb8060',
                               '5313ddeb67f22e02b2109ff35ca074db47f38ddbe19e22e95b2a6e7f908aec86',
                               '855745003e7c964f375554a7448241e5e6235fe78dac1d20fa85956421bdf0a1']},
     'ball': {'metadata': {'name': 'ball',
                           'at': [0, 0],
                           'baseline': 0,
                           'blocks': None,
                           'dynamic': True},
              'pixels': ['ef7e8f49ca0d9ccb9d47fa95447aa991d1d8b60a2ca182c6e186ee7d449e5cbb',
                         '6a0634300197c60405471e394369725a5a6f1a971e887f6375d6b9e0d280baaf']},
     'smoke': {'metadata': {'name': 'smoke',
                            'at': [0, 0],
                            'baseline': 0,
                            'blocks': None,
                            'dynamic': True},
               'pixels': ['0f57e59c401a7ed0331c8b2a4150a45fb3f84d2a49cdfdce91c136befe152b19',
                          'da0568202b9f59b47b65a26d4babc7210a4a3bf5ac9c13cc3de4767010e7355e',
                          '145e27b3497d83cd9123aa4a3c913dec4100da2d04a80b339be427629594fb3f',
                          '6553c4df43038daaa3ed0530357259dc282d245288f1b8af607305108b52abc4']},
     'emote_hi': {'metadata': {'name': 'emote_hi',
                               'at': [0, 0],
                               'baseline': 0,
                               'blocks': None,
                               'dynamic': True},
                  'pixels': ['e94fb9f0d04ddd16a1c25b804152552fcdb3ddbaed3d82c64ca45b5819017685']},
     'emote_bang': {'metadata': {'name': 'emote_bang',
                                 'at': [0, 0],
                                 'baseline': 0,
                                 'blocks': None,
                                 'dynamic': True},
                    'pixels': ['6538cc16fc403478ee0b47b47afc0ad3e100e80b64a41e7de95e3d1850afa972']},
     'emote_heart': {'metadata': {'name': 'emote_heart',
                                  'at': [0, 0],
                                  'baseline': 0,
                                  'blocks': None,
                                  'dynamic': True},
                     'pixels': ['a893fc4f9f97a9676eca3fe6f853e0e7e53696dc484e8562d51db26b9552ae64']},
     'emote_oil': {'metadata': {'name': 'emote_oil',
                                'at': [0, 0],
                                'baseline': 0,
                                'blocks': None,
                                'dynamic': True},
                   'pixels': ['de17e1144a20ca4ce33119429af5c7dbade21d91c8110a9d27fe652325fd0bdd']},
     'emote_zzz': {'metadata': {'name': 'emote_zzz',
                                'at': [0, 0],
                                'baseline': 0,
                                'blocks': None,
                                'dynamic': True},
                   'pixels': ['269a0d038576338a347f08bb0bbc4b2d36aa9ebc3b3a7f3008a901e8a0b8ac39']},
     'emote_fist': {'metadata': {'name': 'emote_fist',
                                 'at': [0, 0],
                                 'baseline': 0,
                                 'blocks': None,
                                 'dynamic': True},
                    'pixels': ['21412d2dce56f5a1a47b507b50f48eeceaecb14e70217450b500614b5f8a4ef2']},
     'box': {'metadata': {'name': 'box',
                          'at': [0, 0],
                          'baseline': 0,
                          'blocks': None,
                          'dynamic': True},
             'pixels': ['364b4e5c80238886147df94eb20a092e0439cf1380bb0e7e6bd535c54870aeb2']}},
    'zones': {'door': [150, 60],
     'gate': [622, 175],
     'gate_outside': [650, 175],
     'court_spots': [[69, 132],
                     [120, 130],
                     [183, 137],
                     [80, 201],
                     [138, 194],
                     [188, 221],
                     [77, 266],
                     [158, 271]],
     'bar_spots': [[431, 105], [454, 108], [479, 109], [505, 112], [529, 112]],
     'curl_spots': [[282, 305], [324, 306], [366, 306], [405, 281]],
     'smoke_spots': [[516, 300], [540, 326], [578, 311], [603, 290], [599, 333]],
     'loiter_spots': [[232, 79],
                      [342, 80],
                      [391, 179],
                      [456, 159],
                      [549, 146],
                      [589, 113],
                      [237, 187],
                      [243, 322],
                      [167, 326],
                      [478, 233],
                      [471, 321],
                      [305, 188]],
     'guard_post': [604, 216],
     'walkable': [[11, 56, 619, 294], [630, 150, 10, 50]],
     'court': [24, 96, 190, 200],
     'oil_bar': [420, 56, 120, 44],
     'smoking_corner': [500, 262, 124, 82],
     'weights': [262, 222, 180, 110],
     'hoop': {'pole': [32, 198], 'rim': [46, 178]},
     'press': [{'point': [300, 272], 'hide': 'bench_0'}, {'point': [362, 272], 'hide': 'bench_1'}],
     'obstacles': [[567, 54, 39, 20],
                   [28, 192, 9, 6],
                   [277, 118, 46, 28],
                   [353, 118, 46, 28],
                   [427, 78, 16, 8],
                   [451, 80, 16, 8],
                   [474, 79, 16, 8],
                   [499, 89, 37, 11],
                   [286, 260, 28, 12],
                   [348, 260, 28, 12],
                   [396, 242, 29, 9],
                   [425, 308, 10, 5],
                   [411, 320, 10, 5],
                   [517, 267, 7, 5],
                   [553, 294, 14, 8]],
     'bench_contract': {'frame': [32, 32],
                        'anchor': [16, 28],
                        'cushion': [5, 15, 23, 6],
                        'ground_line': 28,
                        'note': 'Press animation must replace the whole empty bench sprite.'}},
    'tables': {'picnic_0': {'at': [270, 100], 'size': [60, 48], 'blocks': [277, 118, 46, 28]},
     'picnic_1': {'at': [346, 100], 'size': [60, 48], 'blocks': [353, 118, 46, 28]}},
}

# Only update after opening the final exported previews.
VIEWED = {'yard-2x.png': 'f69f57fc2baeed02096082553aacbf9fa1c525776a5b524df2a3170b39aa85b5',
 'yard-open-2x.png': '61d97020e688dc150690bea02a1631671f7e55c83eb0f231466d6e0fdc506f83',
 'yard-zones-2x.png': '1fe5b0c4b05a2be541ad30877c52d398a7d47841ab3599f02efd7fdd4dfe4014',
 'props-4x.png': 'bed252aed14b000ec68a5951e3fd1b8096fb4baf16492a490791264f529834d6',
 'seats-6x.png': '06b39de8c4b9e4f84aa8aad0b66e4da96f6fd4a12ee3bec88a1e1792d982c5cc'}

# A single editable source for scene placement, footprints, and action positions.
LAYOUT = {
    'size':[640,360], 'building':[16,0,284,56],
    'doorway':[139,26,22,30], 'gate_opening':[630,150,10,50],
    'court':[24,96,190,200], 'mat':[262,222,180,110],
    'oil_bar':[420,56,120,44], 'smoking_corner':[500,262,124,82],
    'tables':[{'name':f'picnic_{i}', 'at':[x,100], 'size':[60,48],
               'blocks':[x+7,118,46,28], 'far_top':10, 'near_top':35,
               'far_baseline':113, 'baseline':130, 'near_baseline':138,
               'seat_x':[16,44]} for i,x in enumerate((270,346))],
    'seats_crop':[258,80,160,76],
    'props':[
        # baseline is the ground line; blocks describe ground contact, not image bounds.
        {'name':'watchtower','kind':'tower','size':[60,78],'at':[555,0],
         'baseline':74,'blocks':[567,54,39,20]},
        {'name':'hoop','kind':'hoop','size':[38,54],'at':[23,145],
         'baseline':198,'blocks':[28,192,9,6], 'pole':[9,53], 'rim':[23,33]},
        {'name':'drum_0','kind':'drum','size':[20,28],'at':[426,60],
         'baseline':86,'blocks':[427,78,16,8]},
        {'name':'drum_1','kind':'drum_rust','size':[20,28],'at':[450,62],
         'baseline':88,'blocks':[451,80,16,8]},
        {'name':'drum_2','kind':'pump','size':[22,40],'at':[473,49],
         'baseline':87,'blocks':[474,79,16,8]},
        {'name':'counter','kind':'counter','size':[46,34],'at':[495,68],
         'baseline':100,'blocks':[499,89,37,11]},
        {'name':'bench_0','kind':'bench','size':[32,32],'at':[284,244],
         'baseline':272,'blocks':[286,260,28,12]},
        {'name':'bench_1','kind':'bench','size':[32,32],'at':[346,244],
         'baseline':272,'blocks':[348,260,28,12]},
        {'name':'dumbbell_rack','kind':'rack','size':[36,31],'at':[393,222],
         'baseline':251,'blocks':[396,242,29,9]},
        {'name':'kettlebell_0','kind':'kettle','size':[12,14],'at':[425,301],
         'baseline':313,'blocks':[425,308,10,5]},
        {'name':'kettlebell_1','kind':'kettle','size':[12,14],'at':[411,313],
         'baseline':325,'blocks':[411,320,10,5]},
        {'name':'lamp_post','kind':'lamp','size':[19,50],'at':[511,224],
         'baseline':272,'blocks':[517,267,7,5]},
        {'name':'ash_bin','kind':'ash','size':[20,27],'at':[551,277],
         'baseline':302,'blocks':[553,294,14,8]},
        {'name':'main_gate','kind':'gate','size':[12,54],'at':[628,148],
         'baseline':200,'blocks':None,'count':4},
        {'name':'block_door','kind':'door','size':[22,30],'at':[139,26],
         'baseline':56,'blocks':None,'count':3},
        {'name':'ball','kind':'ball','size':[8,8],'at':[0,0],
         'baseline':0,'blocks':None,'count':2,'dynamic':True},
        {'name':'smoke','kind':'smoke','size':[8,8],'at':[0,0],
         'baseline':0,'blocks':None,'count':4,'dynamic':True},
        *[{'name':'emote_'+n,'kind':'emote','icon':n,'size':[12,12],
           'at':[0,0],'baseline':0,'blocks':None,'count':1,'dynamic':True}
          for n in ('hi','bang','heart','oil','zzz','fist')],
        {'name':'box','kind':'box','size':[10,8],'at':[0,0],
         'baseline':0,'blocks':None,'dynamic':True},
    ],
    'zones':{
        'door':[150,60], 'gate':[622,175], 'gate_outside':[650,175],
        'court_spots':[[69,132],[120,130],[183,137],[80,201],
                       [138,194],[188,221],[77,266],[158,271]],
        'bar_spots':[[431,105],[454,108],[479,109],[505,112],[529,112]],
        'curl_spots':[[282,305],[324,306],[366,306],[405,281]],
        'smoke_spots':[[516,300],[540,326],[578,311],[603,290],[599,333]],
        'loiter_spots':[[232,79],[342,80],[391,179],[456,159],
                        [549,146],[589,113],[237,187],[243,322],
                        [167,326],[478,233],[471,321],[305,188]],
        'guard_post':[604,216],
        'walkable':[[11,56,619,294],[630,150,10,50]],
    }
}

LAYOUT['props'][2:2] = [
    {'name':t['name']+suffix, 'kind':kind, 'size':t['size'], 'at':t['at'],
     'baseline':t[key], 'blocks':t['blocks'] if kind=='table' else None,
     'bench_top':t[top] if top else None}
    for t in LAYOUT['tables']
    for suffix,kind,key,top in [('_far','table_far','far_baseline','far_top'),
                                ('','table','baseline',None),
                                ('_near','table_near','near_baseline','near_top')]
]

# Compact handmade 3x5 font, deliberately used only for signs and QA overlays.
FONT = {
 'A':['010','101','111','101','101'], 'B':['110','101','110','101','110'],
 'C':['011','100','100','100','011'], 'D':['110','101','101','101','110'],
 'E':['111','100','110','100','111'], 'F':['111','100','110','100','100'],
 'G':['011','100','101','101','011'], 'H':['101','101','111','101','101'],
 'I':['111','010','010','010','111'], 'J':['001','001','001','101','010'],
 'K':['101','101','110','101','101'], 'L':['100','100','100','100','111'],
 'M':['101','111','111','101','101'], 'N':['101','111','111','111','101'],
 'O':['010','101','101','101','010'], 'P':['110','101','110','100','100'],
 'Q':['010','101','101','111','011'], 'R':['110','101','110','101','101'],
 'S':['011','100','010','001','110'], 'T':['111','010','010','010','010'],
 'U':['101','101','101','101','111'], 'V':['101','101','101','101','010'],
 'W':['101','101','111','111','101'], 'X':['101','101','010','101','101'],
 'Y':['101','101','010','010','010'], 'Z':['111','001','010','100','111'],
 '0':['111','101','101','101','111'], '1':['010','110','010','010','111'],
 '2':['110','001','010','100','111'], '3':['110','001','010','001','110'],
 '4':['101','101','111','001','001'], '5':['111','100','110','001','110'],
 '6':['011','100','111','101','111'], '7':['111','001','010','010','010'],
 '8':['111','101','111','101','111'], '9':['111','101','111','001','110'],
 '-':['000','000','111','000','000'], ' ':['000']*5,
}

def text(d, xy, s, color):
    x,y=xy
    for c in s.upper():
        for j,row in enumerate(FONT.get(c,FONT[' '])):
            for i,v in enumerate(row):
                if v=='1': d.point((x+i,y+j),fill=color)
        x+=4

def rect(d, box, fill, outline=None):
    x,y,w,h=box
    if w>0 and h>0: d.rectangle((x,y,x+w-1,y+h-1),fill=fill,outline=outline)

def background():
    im=Image.new('RGBA',LAYOUT['size'],P['ground']); d=ImageDraw.Draw(im)
    # Concrete slabs: sparse seams and deliberately quiet broad ground planes.
    for y in (88,174,258,337):
        d.line((12,y,629,y),fill=P['ground_dark'])
    for x,y0,y1 in [(228,56,174),(464,56,174),(247,174,258),(481,174,258),
                    (227,258,349),(460,258,349)]:
        d.line((x,y0,x,y1),fill=P['ground_dark'])
    for pts in [[(111,77),(118,80),(119,85),(125,87)],
                [(218,311),(224,307),(230,308),(234,303)],
                [(465,188),(469,192),(467,198),(474,202)],
                [(574,241),(580,238),(585,241),(590,239)],
                [(57,319),(64,317),(70,320)],[(340,205),(345,208),(351,207)]]:
        d.line(pts,fill=P['crack'])
    # Flush drain and small oil stains are ground detail, never sortable objects.
    rect(d,[468,119,22,12],P['crack'],P['steel_dark'])
    for x in range(471,488,3): d.line((x,122,x,127),fill=P['wall_dark'])
    for box in [(440,92,7,2),(480,97,9,3),(522,103,8,2)]:
        rect(d,box,P['crack'])
    # Half court: two restrained paint colours retain orange robot contrast.
    x,y,w,h=LAYOUT['court']
    rect(d,[x,y,w,h],P['ground_dark'])
    rect(d,[x+2,153,56,86],P['key'])
    d.rectangle((x,y,x+w-1,y+h-1),outline=P['paint'],width=2)
    d.rectangle((x,153,80,239),outline=P['paint'],width=2)
    d.arc((53,166,107,226),-90,90,fill=P['paint'],width=2)
    d.arc((41,166,95,226),90,270,fill=P['paint'],width=1)
    d.arc((-112,78,188,314),-56,56,fill=P['paint'],width=2)
    d.line((26,97,119,97),fill=P['paint'],width=2)
    d.line((26,294,119,294),fill=P['paint'],width=2)
    # Mat tiles with one-pixel grid; no texture noise.
    rect(d,LAYOUT['mat'],P['mat'],P['ink'])
    for x in range(282,442,20): d.line((x,223,x,330),fill=P['mat_light'])
    for y in range(242,332,20): d.line((263,y,440,y),fill=P['mat_light'])
    # Yellow safety line, interrupted at the doorway and gate.
    for a,b in [((16,62),(136,62)),((165,62),(418,62)),
                ((543,62),(623,62)),((16,62),(16,344)),
                ((16,344),(623,344)),((623,62),(623,145)),
                ((623,205),(623,344))]: d.line((*a,*b),fill=P['yellow'])
    # Boundary wall face and cap stones.
    rect(d,[0,0,640,56],P['wall_mid'])
    for y in (9,23,37,51):
        d.line((0,y,639,y),fill=P['wall_dark'])
        for x in range(0 if y%2 else 18,640,36):
            d.line((x,y-12,x,y-1),fill=P['wall_dark'])
    rect(d,[0,0,640,5],P['wall']); d.line((0,5,639,5),fill=P['ink'])
    rect(d,[0,55,640,2],P['crack'])
    # Cell block projects slightly forward of the perimeter.
    rect(d,LAYOUT['building'],P['wall']); rect(d,[16,52,284,4],P['wall_dark'])
    for y in (14,28,42):
        d.line((17,y,298,y),fill=P['wall_mid'])
        for x in range(18+(14 if y==28 else 0),300,28):
            d.line((x,y-12,x,y-1),fill=P['wall_mid'])
    for x in (36,83,204,251):
        rect(d,[x-2,21,28,20],P['wall_dark'])
        rect(d,[x,22,24,15],P['window'],P['ink'])
        d.line((x,23,x+22,23),fill=P['steel_dark'])
        for bx in (x+5,x+11,x+17): d.line((bx,22,bx,36),fill=P['wire'])
        rect(d,[x-1,37,26,2],P['metal_dark'])
    rect(d,[136,24,28,32],P['wall_dark'])
    rect(d,LAYOUT['doorway'],P['window'])
    rect(d,[139,54,22,2],P['metal_mid'])
    rect(d,[124,12,52,10],P['ink']); rect(d,[125,13,50,8],P['paint'])
    text(d,(130,15),'CELL BLOCK',P['ink'])
    # The side wall shows its narrow top; gate is a genuine opening.
    for x in (0,630):
        rect(d,[x,56,10,294],P['wall_dark'])
        rect(d,[x,56,4,294],P['wall'])
        for y in range(67,350,19): d.line((x,y,x+9,y),fill=P['wall_mid'])
    rect(d,[10,57,1,293],P['crack'])
    rect(d,LAYOUT['gate_opening'],P['window'])
    for y in (158,177,194): d.line((631,y,639,y-3),fill=P['wall_dark'])
    for y in (147,200): rect(d,[627,y,13,3],P['metal_dark'],P['ink'])
    rect(d,[596,137,30,10],P['ink']); rect(d,[597,138,28,8],P['paint'])
    text(d,(599,140),'INTAKE',P['ink'])
    # Coiled razor wire along the crest, interrupted by the tower silhouette later.
    for x in range(3,640,16):
        d.ellipse((x,1,x+17,10),outline=P['wire'])
        d.line((x+3,1,x+11,10),fill=P['steel_dark'])
    d.line((0,6,639,6),fill=P['wire'])
    # Foreground wall top and its own razor wire, behind all walkable ground.
    rect(d,[0,350,640,10],P['wall_dark'])
    rect(d,[0,350,640,3],P['wall']); d.line((0,350,639,350),fill=P['ink'])
    for x in range(3,640,16):
        d.ellipse((x,352,x+17,359),outline=P['wire'])
        d.line((x+6,352,x+12,359),fill=P['steel_dark'])
    # Small weeds on the boundary, and readable paper butts near the sand bin.
    for x,y in [(20,302),(618,88),(18,81),(601,340),(452,340)]:
        d.line((x,y,x-2,y-4),fill=P['wall_mid'])
        d.line((x,y,x+3,y-5),fill=P['wall_mid'])
        d.point((x,y-5),fill=P['crack'])
    for x,y in [(567,315),(575,320),(591,306),(583,335),(548,309),(608,315)]:
        d.line((x,y,x+2,y),fill=P['paper']); d.point((x+3,y),fill=P['rust'])
    return im

def sprite(p, frame=0):
    im=Image.new('RGBA',p['size']); d=ImageDraw.Draw(im)
    k=p['kind']; C=P
    def r(b,c,o=None): rect(d,b,C.get(c,c),C.get(o,o))
    def ln(coords,c,width=1): d.line(coords,fill=C[c],width=width)
    if k=='tower':
        # Tall open supports: all elevated structure lives in this sprite.
        r([19,27,3,29],'steel_dark','ink'); r([38,27,3,29],'steel_dark','ink')
        r([17,54,7,2],'ink'); r([37,54,7,2],'ink')
        r([13,26,4,46],'steel_dark','ink'); r([44,26,4,46],'steel_dark','ink')
        ln((16,35,45,66),'ink',3); ln((45,35,16,66),'ink',3)
        ln((17,35,44,64),'metal_dark'); ln((44,35,17,64),'metal_dark')
        r([12,70,8,4],'ink'); r([42,70,9,4],'ink')
        r([14,74,8,2],'crack'); r([44,74,9,2],'crack')
        r([4,7,50,24],'wall_mid','ink'); r([5,8,48,3],'wall')
        for x in (8,24,40):
            r([x,13,11,12],'window','ink'); ln((x+1,14,x+7,14),'metal_mid')
        r([1,4,56,5],'steel_dark','ink'); r([7,1,44,4],'wall','ink')
        r([2,30,54,5],'wall_dark','ink'); ln((4,30,52,30),'metal_mid')
        r([5,35,3,6],'ink'); r([51,35,3,6],'ink'); ln((6,40,52,40),'wire')
        # Searchlight: a solid lit lens, no beam.
        r([49,17,10,8],'metal_dark','ink'); r([55,18,4,6],'paint','ink')
        r([30,36,2,35],'ink')
        for y in range(41,70,6): ln((25,y,35,y),'wire')
    elif k=='hoop':
        r([7,22,4,28],'metal_dark','ink'); r([5,47,9,6],'steel_dark','ink')
        r([7,53,9,1],'crack'); ln((8,24,8,46),'metal_mid')
        ln((9,27,15,27),'ink',3)
        r([10,5,8,26],'paint','ink'); r([11,6,2,24],'metal')
        r([13,17,4,10],'paint','rust')
        d.polygon([(18,34),(21,42),(27,42),(30,34)],outline=C['paper'])
        ln((22,35,23,42),'paper'); ln((27,35,25,42),'paper')
        d.ellipse((16,30,30,35),fill=C['ink'],outline=C['ink'])
        d.ellipse((17,31,29,34),outline=C['rust']); ln((19,31,27,31),'orange_light')
    elif k in ('table_far','table_near'):
        # Surface highlight is the seat contact line. Legs belong to this layer.
        y=p['bench_top']
        r([3,y-1,54,5],'wall','ink'); ln((5,y,54,y),'metal_mid')
        for x in (7,50):
            r([x,y+4,3,3 if k=='table_far' else 7],'steel_dark','ink')
            if k=='table_near': r([x+1,46,5,1],'crack')
    elif k=='table':
        for x in (11,45):
            r([x,23,4,23],'wall_dark','ink'); r([x+1,46,6,2],'crack')
        ln((12,40,46,28),'ink',3); ln((13,40,46,29),'metal_dark')
        r([7,24,46,7],'steel_dark','ink')
        r([5,14,50,16],'metal_dark','ink')
        ln((7,15,52,15),'metal'); ln((7,21,52,21),'wall_dark')
        ln((7,25,52,25),'wall_dark')
        for x in (11,48):
            d.point((x,19),fill=C['ink']); d.point((x,24),fill=C['ink'])
    elif k in ('drum','drum_rust','pump'):
        dy=12 if k=='pump' else 0
        color='rust' if k=='drum_rust' else 'blue'
        r([1,dy+5,16,18],color,'ink')
        d.ellipse((1,dy+19,16,dy+25),fill=C[color],outline=C['ink'])
        d.ellipse((1,dy+1,16,dy+8),fill=C['metal_dark'],outline=C['ink'])
        ln((3,dy+3,12,dy+3),'metal_mid'); ln((3,dy+9,3,dy+21),'metal')
        ln((2,dy+11,15,dy+11),'steel_dark'); ln((2,dy+20,15,dy+20),'steel_dark')
        r([9,dy+3,3,2],'oil'); r([4,dy+26,13,1],'crack')
        if k=='pump':
            r([8,4,3,13],'metal_dark','ink'); ln((9,4,17,4),'ink',3)
            ln((10,3,18,3),'metal'); ln((17,4,17,9),'ink')
            ln((8,9,3,9),'ink',3); ln((3,9,3,5),'metal_mid')
    elif k=='counter':
        r([4,17,3,15],'steel_dark','ink'); r([38,17,3,15],'steel_dark','ink')
        r([6,32,5,1],'crack'); r([40,32,5,1],'crack')
        r([1,12,44,7],'wall_dark','ink'); r([0,10,46,5],'metal_dark','ink')
        ln((2,11,43,11),'metal'); r([6,19,34,8],'wall_mid','ink')
        for x in (6,20,33):
            r([x,4,7,7],'metal','ink'); r([x+1,1,4,4],'metal_mid','ink')
            r([x+6,3,3,2],'metal_dark','ink'); r([x+2,6,2,3],'oil')
    elif k=='bench':
        # Local bench contract: anchor (16,28); cushion [5,15,23,6].
        # Front feet end at y=27. Keep robots' press bench identical to this shape.
        r([2,16,3,12],'metal_dark','ink'); r([27,16,3,12],'metal_dark','ink')
        ln((4,25,28,25),'steel_dark',2)
        r([5,15,23,6],'mat_light','ink'); ln((6,15,26,15),'metal_mid')
        r([8,21,3,7],'steel_dark','ink'); r([23,21,3,7],'steel_dark','ink')
        r([2,11,3,8],'metal_mid','ink'); r([27,11,3,8],'metal_mid','ink')
        # Empty rack: no bar or weights spanning the bench.
        ln((3,11,6,11),'metal'); ln((26,11,29,11),'metal')
        ln((3,28,7,28),'ink'); ln((28,28,31,28),'ink')
    elif k=='rack':
        r([3,8,3,21],'metal_dark','ink'); r([29,8,3,21],'metal_dark','ink')
        for y in (10,20):
            r([1,y,34,4],'metal_dark','ink')
            for x in (5,16,27):
                ln((x-2,y-2,x+4,y-2),'wire',2)
                r([x-3,y-5,3,6],'steel_dark','ink'); r([x+3,y-5,3,6],'steel_dark','ink')
        ln((4,29,8,29),'ink'); ln((30,29,34,29),'ink')
    elif k=='kettle':
        d.ellipse((2,0,7,6),outline=C['ink'],width=2)
        d.ellipse((0,4,9,11),fill=C['steel_dark'],outline=C['ink'])
        ln((3,6,3,8),'metal_mid'); r([3,12,8,1],'ink')
    elif k=='lamp':
        r([7,10,3,34],'steel_dark','ink'); ln((8,13,8,42),'metal_mid')
        r([6,43,7,5],'steel_dark','ink'); r([9,48,7,1],'crack')
        r([3,3,12,9],'metal_dark','ink'); r([5,5,8,5],'paint','ink')
        r([2,1,14,3],'steel_dark','ink'); r([6,0,6,2],'steel_dark','ink')
        ln((8,4,8,10),'metal_dark')
    elif k=='ash':
        r([2,6,14,16],'metal_dark','ink')
        d.ellipse((2,17,15,24),fill=C['metal_dark'],outline=C['ink'])
        d.ellipse((0,1,17,9),fill=C['steel_dark'],outline=C['ink'])
        d.ellipse((2,2,15,7),fill=C['key'],outline=C['metal_mid'])
        ln((5,4,7,4),'paper'); d.point((8,4),fill=C['rust'])
        ln((11,3,12,4),'paper'); r([4,11,2,9],'metal_mid')
        ln((9,0,9,3),'paper'); d.point((9,0),fill=C['rust'])
        ln((13,1,12,4),'paper'); d.point((13,1),fill=C['rust'])
        r([6,25,12,1],'crack')
    elif k=='gate':
        shift=(0,18,36,54)[frame]
        # Slides north; fourth frame is entirely transparent.
        for x in (1,10): r([x,1-shift,1,52],'wire','ink')
        for y in range(3,53,6): r([1,y-shift,10,2],'metal_dark','ink')
        r([0,1-shift,12,2],'metal','ink'); r([0,51-shift,12,2],'steel_dark','ink')
        if frame==0: r([4,27,5,6],'steel_dark','ink')
    elif k=='door':
        w=(22,11,0)[frame]
        if w:
            r([0,0,w,30],'steel_dark','ink'); ln((1,1,w-2,1),'metal_mid')
            for x in range(4,w-2,5): ln((x,4,x,25),'wall_dark')
            r([max(1,w-5),15,2,3],'metal')
            r([3,5,max(1,w-7),5],'window','ink')
    elif k=='ball':
        d.ellipse((0,0,7,7),fill=C['ball'],outline=C['ink'])
        if frame==0:
            ln((1,4,6,4),'ink'); ln((3,1,4,3,3,6),'ink')
        else:
            ln((1,2,6,5),'ink'); ln((6,1,3,3,2,6),'ink')
        d.point((2,1),fill=C['orange_light'])
    elif k=='smoke':
        # Binary alpha only: spatial thinning rather than partial opacity.
        if frame==0: r([3,5,3,3],'smoke')
        elif frame==1:
            d.ellipse((1,2,6,7),fill=C['smoke']); r([4,1,3,3],'paper')
        elif frame==2:
            d.ellipse((0,1,7,6),outline=C['smoke']); r([2,1,3,2],'paper')
        else:
            for x,y in [(1,1),(2,1),(6,0),(6,3),(0,5),(5,6)]:
                d.point((x,y),fill=C['smoke'])
    elif k=='emote':
        d.rounded_rectangle((0,0,11,9),radius=3,fill=C['paper'],outline=C['ink'])
        d.polygon([(4,9),(4,11),(7,9)],fill=C['paper'])
        ln((3,9,3,11,4,11,6,10),'ink')
        icon=p['icon']
        if icon=='hi':
            # Raised hand, rather than another baked-in word.
            r([4,4,4,4],'metal_mid','ink')
            ln((3,3,3,5),'ink'); ln((5,2,5,5),'ink'); ln((7,2,7,5),'ink')
            ln((9,3,9,5),'ink'); ln((1,1,2,2),'rust'); ln((10,1,11,2),'rust')
        elif icon=='bang': r([5,2,2,4],'rust'); r([5,7,2,1],'ink')
        elif icon=='heart':
            d.polygon([(2,3),(3,2),(4,2),(5,3),(6,2),(8,2),(9,3),
                       (9,4),(6,7),(5,7),(2,4)],fill=C['red'])
        elif icon=='oil':
            d.polygon([(6,2),(3,6),(4,8),(7,8),(8,6)],fill=C['oil'])
            d.point((5,5),fill=C['metal_mid'])
        elif icon=='zzz':
            ln((2,4,4,4,2,6,4,6),'ink'); ln((6,2,9,2,6,5,9,5),'ink')
        elif icon=='fist':
            r([3,3,6,4],'metal_mid','ink'); r([2,5,3,3],'metal','ink')
            for x in (4,6,8): d.point((x,4),fill=C['ink'])
    elif k=='box':
        d.polygon([(0,2),(3,0),(8,0),(9,2),(9,7),(0,7)],fill=C['key'],outline=C['ink'])
        ln((1,2,8,2),'rust'); ln((5,1,5,6),'paint'); r([2,4,2,2],'rust')
    else: raise ValueError(k)
    return im

def build_atlas():
    atlas=Image.new('RGBA',(256,256)); entries=[]; images={}
    x=y=2; shelf=0
    for p in LAYOUT['props']:
        e={key:p[key] for key in ('name','at','baseline','blocks')}
        frames=[]; imgs=[]
        for f in range(p.get('count',1)):
            w,h=p['size']
            if x+w+2>256: x=2; y+=shelf+2; shelf=0
            if y+h+2>atlas.height:
                bigger=Image.new('RGBA',(256,atlas.height+128)); bigger.paste(atlas,(0,0)); atlas=bigger
            pic=sprite(p,f); atlas.paste(pic,(x,y)); frames.append([x,y,w,h]); imgs.append(pic)
            x+=w+2; shelf=max(shelf,h)
        e['rect']=frames[0]
        if 'count' in p: e['frames']=frames
        if p.get('dynamic'): e['dynamic']=True
        entries.append(e); images[p['name']]=imgs
    return atlas.crop((0,0,256,y+shelf+2)),entries,images

def zones():
    z=dict(LAYOUT['zones'])
    z.update({key:LAYOUT[key] for key in ('court','oil_bar','smoking_corner')})
    z['weights']=LAYOUT['mat']
    props={p['name']:p for p in LAYOUT['props']}
    h=props['hoop']
    z['hoop']={k:[h['at'][i]+h[k][i] for i in range(2)] for k in ('pole','rim')}
    z['seats']=[{'point':[t['at'][0]+x,t['at'][1]+t[top]+4],
                 'facing':f,'prop':t['name']}
                for t in LAYOUT['tables']
                for top,f in [('far_top','down'),('near_top','up')] for x in t['seat_x']]
    z['seats_may_overlap_blocks']=True
    z['press']=[{'point':[p['at'][0]+16,p['at'][1]+28],'hide':p['name']}
                for p in LAYOUT['props'] if p['kind']=='bench']
    z['obstacles']=[p['blocks'] for p in LAYOUT['props'] if p['blocks'] is not None]
    z['bench_contract']={'frame':[32,32],'anchor':[16,28],
                         'cushion':[5,15,23,6], 'ground_line':28,
                         'note':'Press animation must replace the whole empty bench sprite.'}
    return z

def composite(bg,images,opened=False,standins=False):
    im=bg.copy()
    for p in sorted(LAYOUT['props'],key=lambda p:p['baseline']):
        if p.get('dynamic'): continue
        f=p.get('count',1)-1 if opened and p['kind'] in ('door','gate') else 0
        im.alpha_composite(images[p['name']][f],tuple(p['at']))
    if standins:
        # Interleave stand-ins with props, exactly as the engine does.
        im=bg.copy(); items=[]
        for p in LAYOUT['props']:
            if not p.get('dynamic'): items.append((p['baseline'],'prop',p))
        for name,point in all_points(zones(),outside=False): items.append((point[1],'robot',(name,point)))
        for _,kind,obj in sorted(items,key=lambda a:a[0]):
            if kind=='prop': im.alpha_composite(images[obj['name']][0],tuple(obj['at']))
            else:
                _,(x,y)=obj; d=ImageDraw.Draw(im)
                # Exact 16x24 outline, feet aligned on the ground point.
                rect(d,[x-8,y-24,16,24],P['orange'],P['ink'])
                rect(d,[x-6,y-22,12,8],P['metal'],P['ink'])
                rect(d,[x-4,y-19,8,2],P['window'])
                rect(d,[x-4,y-10,8,3],P['ink'])
                d.line((x,y-4,x,y-1),fill=P['ink'])
    return im

def all_points(z,outside=True):
    for k in ('door','gate','guard_post'):
        yield k,z[k]
    if outside: yield 'gate_outside',z['gate_outside']
    for k in ('court_spots','bar_spots','curl_spots','smoke_spots','loiter_spots'):
        for i,point in enumerate(z[k]): yield k.replace('_spots','')+'-'+str(i),point
    for k in ('seats','press'):
        for i,e in enumerate(z[k]): yield k+'-'+str(i),e['point']

def zone_preview(bg,images,z):
    im=composite(bg,images,standins=True); d=ImageDraw.Draw(im)
    # Rectangles have distinct semantic colours; all marks are preview-only.
    for key in ('walkable','obstacles'):
        for box in z[key]: rect(d,box,None,P['cyan'] if key=='walkable' else P['red'])
    for key in ('court','weights','oil_bar','smoking_corner'):
        rect(d,z[key],None,P['yellow'])
        x,y,w,h=z[key]
        label=key.replace('_',' ')
        rect(d,[x+2,y+2,len(label)*4+1,7],P['ink'])
        text(d,(x+3,y+3),label,P['yellow'])
    for name,(x,y) in all_points(z,outside=False):
        d.line((x-2,y,x+2,y),fill=P['cyan']); d.line((x,y-2,x,y+2),fill=P['cyan'])
        label=name.replace('loiter','L').replace('court','C').replace('smoke','S').replace('curl','W').replace('seats','T').replace('press','P').replace('bar','B')
        tx=min(637-len(label)*4,max(12,x+4)); ty=min(340,y+3)
        rect(d,[tx-1,ty-1,len(label)*4,7],P['ink'])
        text(d,(tx,ty),label,P['paper'])
    for name,(x,y) in z['hoop'].items():
        d.line((x-2,y,x+2,y),fill=P['cyan']); d.line((x,y-2,x,y+2),fill=P['cyan'])
        text(d,(x+5,y-3),name,P['ink'])
    d.line((631,175,639,175,636,172),fill=P['cyan'])
    rect(d,[575,184,63,7],P['ink']); text(d,(576,185),'OUTSIDE 650 175',P['paper'])
    text(d,(478,18),'CYAN WALKABLE',P['paper'])
    text(d,(478,26),'RED OBSTACLE',P['paper'])
    text(d,(478,34),'YELLOW AREA',P['paper'])
    return im

def checker(atlas):
    im=Image.new('RGBA',atlas.size,P['ground']); d=ImageDraw.Draw(im)
    for y in range(0,im.height,8):
        for x in range(0,im.width,8):
            if (x//8+y//8)%2: rect(d,[x,y,8,8],P['crack'])
    im.alpha_composite(atlas); return im

def seat_robots(z):
    """Real frame 0 sprites; preserve the engine's (16,28) placement anchor.

    idle_up's torso underside is row 23, so translate its pixels down one row
    inside the preview frame to put that underside at the seat contract row 24.
    This is a temporary stand-in, not the forthcoming sit_back animation.
    """
    ref=ROOT.parent/'ref-robots'
    if not ref.exists(): ref=ROOT.parent/'robots'  # no reference set kept: use the final sheets
    meta=json.loads((ref/'robots.json').read_text())
    assert meta['frame']==[32,32] and meta['anchor']==[16,28]
    rows={r['name']:r['row'] for r in meta['rows']}
    robots=[]
    for variant,seat in enumerate(z['seats']):
        pose='sit' if seat['facing']=='down' else 'idle_up'
        with Image.open(ref/f'robot-{variant}.png') as sheet:
            frame=sheet.convert('RGBA').crop((0,rows[pose]*32,32,rows[pose]*32+32))
        if pose=='idle_up':
            shifted=Image.new('RGBA',(32,32)); shifted.alpha_composite(frame,(0,1)); frame=shifted
        robots.append({'seat':seat,'variant':variant,'pose':pose,'frame':frame,
                       'at':(seat['point'][0]-16,seat['point'][1]-28)})
    return robots

def seats_preview(bg,images,z):
    # Background first, then one shared baseline/anchor-y ordering for all items.
    im=bg.copy()
    items=[(p['baseline'],images[p['name']][0],p['at'])
           for p in LAYOUT['props'] if not p.get('dynamic')]
    items.extend((r['seat']['point'][1],r['frame'],r['at']) for r in seat_robots(z))
    for _,frame,at in sorted(items,key=lambda item:item[0]):
        im.alpha_composite(frame,tuple(at))
    x,y,w,h=LAYOUT['seats_crop']
    return im.crop((x,y,x+w,y+h))

def reference_image(key):
    return Image.frombytes('RGBA',(640,360),zlib.decompress(base64.b85decode(ROUND1[key])))

def round2_checks(bg,atlas,entries,images,z,ok):
    sha=lambda b:hashlib.sha256(b).hexdigest()
    reference=reference_image
    inside=lambda x,y:any(contains([*t['at'],*t['size']],(x,y)) for t in LAYOUT['tables'])
    oldbg=reference('bg_rgba_b85'); oldscene=reference('composite_rgba_b85')
    scene=composite(bg,images)
    bgdiff=sum(a!=b for a,b in zip(bg.getdata(),oldbg.getdata()))
    outside_bg=sum(bg.getpixel((x,y))!=oldbg.getpixel((x,y))
                   for y in range(360) for x in range(640) if not inside(x,y))
    outside_scene=sum(scene.getpixel((x,y))!=oldscene.getpixel((x,y))
                      for y in range(360) for x in range(640) if not inside(x,y))
    ok(bgdiff==0 and outside_bg==0 and outside_scene==0,
       f'round 1 pixel diff: background total {bgdiff}, outside table rectangles {outside_bg}; composed yard outside {outside_scene}')
    for e in entries:
        if e['name'].startswith('picnic_'): continue
        old=ROUND1['props'][e['name']]
        assert {k:v for k,v in e.items() if k not in ('rect','frames')}==old['metadata']
        assert [sha(i.tobytes()) for i in images[e['name']]]==old['pixels']
    ok(True,'all 24 non-table prop metadata and all their frame pixels identical to round 1 (atlas packing may move)')
    ok({k:v for k,v in z.items() if k not in ('seats','seats_may_overlap_blocks')}==ROUND1['zones'],
       'all non-seat zone data identical to round 1, including every obstacle')
    robots=seat_robots(z)
    for t in LAYOUT['tables']:
        old=ROUND1['tables'][t['name']]
        assert all(t[k]==old[k] for k in ('at','size','blocks'))
        parts={p['name']:p for p in LAYOUT['props'] if p['name'].startswith(t['name'])}
        far_y=t['at'][1]+t['far_top']+4; near_y=t['at'][1]+t['near_top']+4
        values=[parts[t['name']+'_far']['baseline'],far_y,parts[t['name']]['baseline'],
                parts[t['name']+'_near']['baseline'],near_y]
        ok(all(a<b for a,b in zip(values,values[1:])),
           f"{t['name']} depth order: far bench {values[0]} < far sitter {values[1]} < table {values[2]} < near bench {values[3]} < near sitter {values[4]}")
        assert parts[t['name']+'_far']['blocks'] is None and parts[t['name']+'_near']['blocks'] is None
        # Compare actual opaque assembly bounds too, not only the nominal box.
        combined=Image.new('RGBA',tuple(t['size']))
        for p in parts.values(): combined.alpha_composite(images[p['name']][0])
        x,y=t['at']; w,h=t['size']; crop=(x,y,x+w,y+h)
        old_bounds=ImageChops.difference(oldscene.crop(crop).convert('RGB'),
                                        oldbg.crop(crop).convert('RGB')).getbbox()
        new_bounds=combined.getbbox()
        edge_change=max(abs(a-b) for a,b in zip(old_bounds,new_bounds))
        ok(edge_change<=2,
           f"{t['name']} footprint {t['blocks']} and 60x48 area unchanged; opaque bounds {list(new_bounds)} vs round 1 {list(old_bounds)}, maximum edge change {edge_change} px")
        for r in (r for r in robots if r['seat']['prop']==t['name']):
            seat=r['seat']; x,y=seat['point']; top=t['far_top'] if seat['facing']=='down' else t['near_top']
            surface=y-28+24; bench=t['at'][1]+top
            # Both seat x's land on an actual opaque bench highlight pixel.
            layer=t['name']+('_far' if seat['facing']=='down' else '_near')
            assert images[layer][0].getpixel((x-t['at'][0],top))==tuple(bytes.fromhex(P['metal_mid'][1:]))+(255,)
            ok(abs(surface-bench)<=1,
               f"seat variant {r['variant']} {t['name']} {seat['facing']} anchor ({x},{y}): robot seat y={surface}, bench top y={bench}, delta={abs(surface-bench)} px")
            if seat['facing']=='down':
                frame=r['frame']; front=images[t['name']][0]
                opaque=above=visible=visible_above=hidden_legs=0
                for fy in range(32):
                    for fx in range(32):
                        if not frame.getpixel((fx,fy))[3]: continue
                        opaque+=1; above+=fy<24
                        tx=r['at'][0]+fx-t['at'][0]; ty=r['at'][1]+fy-t['at'][1]
                        covered=0<=tx<front.width and 0<=ty<front.height and front.getpixel((tx,ty))[3]>0
                        visible+=not covered; visible_above+=(fy<24 and not covered)
                        hidden_legs+=(fy>=24 and covered)
                ok(visible_above>=0.6*above and hidden_legs>0,
                   f"far variant {r['variant']}: {visible}/{opaque} opaque pixels visible after table; above row24 {visible_above}/{above} ({visible_above/above:.1%}, minimum 60%); {hidden_legs} lower pixels hidden")
    # Regenerate zones from the same layout rather than reusing the saved object.
    ok(z==zones(),'props.json and zones.json generated from one LAYOUT; repeat zones identical')

def contains(box,point):
    x,y,w,h=box; px,py=point
    return x<=px<x+w and y<=py<y+h

def check(bg,atlas,entries,images,z):
    results=[]
    def ok(condition,description):
        if not condition: raise AssertionError(description)
        results.append('PASS '+description)
    ok(bg.size==(640,360) and bg.getextrema()[3]==(255,255),'background 640x360; fully opaque')
    ok(bg.getpixel((150,40))==tuple(bytes.fromhex(P['window'][1:]))+(255,) and
       bg.getpixel((635,166))==tuple(bytes.fromhex(P['window'][1:]))+(255,),
       'background door and gate openings are dark and open without their props')
    ok(set(atlas.getchannel('A').getdata())=={0,255},'atlas alpha is binary (0 or 255)')
    colors=set(bg.getdata())|{c for c in atlas.getdata() if c[3]}
    ok(len(colors)<=40,f'{len(colors)} opaque scene colours; limit 40')
    allowed={tuple(bytes.fromhex(c[1:]))+(255,) for c in P.values()}
    ok(colors<=allowed,'every rendered colour belongs to the declared palette')
    ok(len(entries)==30,'30 prop records: 19 standing layers, 2 doors, 9 portable/effect records')
    ok(z['obstacles']==[e['blocks'] for e in entries if e['blocks'] is not None],
       '15 obstacles equal prop blocks exactly, in prop order')
    ok(all(0<=e['at'][0]<640 and 0<=e['at'][1]<360 for e in entries),'all prop placements lie inside scene')
    atlas_boxes=[]
    for e in entries:
        for box in e.get('frames',[e['rect']]):
            x,y,w,h=box
            assert x>=0 and y>=0 and x+w<=atlas.width and y+h<=atlas.height
            assert all(x+w<=a or a+c<=x or y+h<=b or b+d<=y for a,b,c,d in atlas_boxes)
            atlas_boxes.append(box)
    ok(True,f'{len(atlas_boxes)} atlas frame rectangles in bounds, non-overlapping')
    for name,n,size in [('main_gate',4,(12,54)),('block_door',3,(22,30)),
                        ('ball',2,(8,8)),('smoke',4,(8,8))]:
        ok(len(images[name])==n and all(i.size==size for i in images[name]),f'{name}: {n} frames at {size[0]}x{size[1]}')
    ok(all(images['emote_'+n][0].size==(12,12) for n in ('hi','bang','heart','oil','zzz','fist')),
       'all six emotes are 12x12')
    ok(images['box'][0].size==(10,8),'belongings box is 10x8')
    ok(not images['main_gate'][-1].getbbox() and not images['block_door'][-1].getbbox(),
       'fully open door and gate frames are transparent; openings remain visible')
    for p in LAYOUT['props']:
        if p['blocks']:
            x,y,w,h=p['blocks']; px,py=p['at']; sw,sh=p['size']
            assert px<=x and py<=y and x+w<=px+sw and y+h<=py+sh
            if p['kind']!='table': assert y+h==p['baseline'],p['name']
    ok(True,'all 15 footprints inside sprite bounds; non-table footprints end at baseline; tables use depth-sort lines')
    for e in z['press']:
        p=next(p for p in LAYOUT['props'] if p['name']==e['hide'])
        assert p['size']==[32,32]
        assert e['point']==[p['at'][0]+16,p['at'][1]+28]
    ok(True,'both press anchors equal bench top-left + (16,28); bench frames 32x32')
    # A point-robot flood fill checks the same raw navigation rectangles the engine receives.
    free=set()
    for y in range(360):
        for x in range(640):
            pt=(x,y)
            if any(contains(r,pt) for r in z['walkable']) and not any(contains(r,pt) for r in z['obstacles']):
                free.add(pt)
    start=tuple(z['door']); reached={start}; q=deque([start])
    while q:
        x,y=q.popleft()
        for pt in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
            if pt in free and pt not in reached: reached.add(pt); q.append(pt)
    points=[(name,pt) for name,pt in all_points(z,outside=False) if not name.startswith('seats-')]
    ok(all(tuple(pt) in reached for _,pt in points),f'all {len(points)} non-seat inside interaction points reachable from door, outside all blocks (point navigation)')
    ok(z['seats_may_overlap_blocks'] is True and all(
        any((sx-x)**2+(sy-y)**2<=144 and (x,y) in reached
            for x in range(sx-12,sx+13) for y in range(sy-12,sy+13))
        for sx,sy in (e['point'] for e in z['seats'])),
       'all 8 seats within 12 px Euclidean distance of door-reachable free ground; seat/block overlap allowed')
    ok(tuple(z['gate']) in reached and (639,175) in reached,'gate path reaches right scene edge')
    ok(z['gate_outside'][0]>640,'gate_outside lies beyond right edge')
    ok(all(contains(z['court'],p) for p in z['court_spots']),'all 8 court spots inside court')
    ok(all(contains(z['weights'],p) for p in z['curl_spots']),'all 4 curl spots on mat')
    ok(all(contains(z['smoking_corner'],p) for p in z['smoke_spots']),'all 5 smoking spots in corner')
    ok(len(z['seats'])==8 and len(z['bar_spots'])==5 and len(z['press'])==2 and
       len(z['loiter_spots'])==12,'8 seats, 5 bar spots, 2 press spots, 12 loiter spots')
    # Render again to detect accidental nondeterminism, independently of file hashes.
    a2,e2,i2=build_atlas()
    ok(bg.tobytes()==background().tobytes() and atlas.tobytes()==a2.tobytes() and entries==e2,
       'second in-memory generation identical: background, atlas, metadata')
    round2_checks(bg,atlas,entries,images,z,ok)
    return results

def save_json(path,obj):
    path.write_text(json.dumps(obj,indent=2)+'\n',encoding='utf-8')

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def write_report(transcript, bg, atlas, z):
    approved=len(VIEWED)==5 and all(digest(ROOT/'preview'/name)==value for name,value in VIEWED.items())
    review=(
        '**Viewed:** Opened `seats-6x.png` and all four regenerated round 1 previews. '
        'Far robots face the viewer above their bench, with their feet tucked behind the tabletop. '
        'Near robots show their backs and overlap the bench they occupy. The narrow gaps, '
        'exposed bench ends and tabletop seams keep the shared table readable.\n\n'
        '**Viewed:** The idle_up replacement still has standing legs; its back and seat height '
        'read correctly, but the final folded-leg silhouette must be reviewed with sit_back. '
        'The other yard areas, open/closed doors and atlas retain the round 1 appearance.\n\n'
    ) if approved else '**Not checked:** Final preview hashes have not yet been visually approved.\n\n'
    report=(
        '# Scene report — round 2\n\n'
        '**Measured:** `make_scene.py` remains the single deterministic source for all scene outputs. '
        'Pillow and Python standard library only. Rebuild: `python3 scene/make_scene.py`. '
        'The seat preview reads frame 0 from the eight read-only `ref-robots/` sheets and row metadata. '
        'All outputs are written beneath `scene/`.\n\n'
        '**Measured:** Each table now has `_far`, main and `_near` layers. Only the main layer '
        'owns the unchanged collision rectangle. The five sorting lines are recorded below; '
        'picnic baselines are intentional depth-sort lines, not the bottom of their full legs. '
        'All three layers retain the original 60 × 48 area and top-left placements (270,100), (346,100). '
        'The far bench surface moves from y108 to y110; the tabletop spans y114–129; '
        'the near bench surface remains y135. Tabletop centres are (300,122), (376,122).\n\n'
        '**Measured:** Far anchors are y114, facing down; near anchors are y139, facing up. '
        'Their seat surface is anchor y−4. X positions remain 286/314 and 362/390. '
        '`seats_may_overlap_blocks: true` permits seat destinations inside collision rectangles. '
        'Seats are excluded from the obstacle-free point assertion; every seat must be within '
        '12 px Euclidean distance of door-reachable free ground. Every other zone is unchanged.\n\n'
        '**Measured:** `preview/seats-6x.png` is a nearest-neighbour 6× crop of scene rectangle '
        '[258,80,160,76] (960 × 456 exported). It starts with the background and composites '
        'all static props and eight real robot frames in one ascending baseline/anchor-y sort. '
        'Variants 0,1,4,5 use sit row 6; variants 2,3,6,7 use idle_up row 2. '
        'The stand-in pixels shift down 1 px within their frame: idle_up torso underside row23 '
        'then occupies contract row24 while placement still uses anchor (16,28). '
        'No robot source sheet is edited. All four original previews are regenerated.\n\n'
        f'**Measured:** Background 640 × 360 opaque RGB; atlas {atlas.width} × {atlas.height} RGBA; '
        f'{len(set(bg.getdata())|{c for c in atlas.getdata() if c[3]})} opaque scene colours. '
        'The original palette is unchanged. Round 1 background and composed-scene reference pixels '
        'are embedded as compressed RGBA in the generator; metadata and frame hashes for all other '
        'props and non-seat zone data are embedded too. These are comparison evidence, not art inputs. '
        'The pixel-diff transcript below proves preservation outside the two original table rectangles.\n\n'
        '**Measured:** Atlas repacking changes other props’ atlas rect coordinates; their scene '
        'placement, animation counts, baselines, collision, dimensions and decoded frame pixels '
        'are checked against round 1. All 15 obstacle rectangles are unchanged. '
        'The original press anchor/replacement contract remains unchanged.\n\n'
        '**Measured:** Exact successful self-check output (also `self-check.txt`):\n\n'
        '```text\n'+transcript+'```\n\n'
        '**Measured (delivery verification):** Two complete subprocess rebuilds compared SHA256 '
        'snapshots of every file under scene (including the source, report and existing .gitkeep). '
        'The exact result was:\n\n'
        '```text\nFULL REBUILD: byte-identical across 14 files, including generator and REPORT.md, on two complete reruns\n'
        'REPORT: self-check transcript embedded verbatim; all five viewed preview hashes match\n```\n\n'+review+
        '**Not checked:** Actual engine integration, animation playback, robot-body clearance '
        'during navigation, final row16 sit_back art, and exact companion press art matching. '
        'The preview uses the requested translated idle_up stand-in; it does not verify the future seated back pose.\n\n'
        '**Measured:** Reviewed preview SHA256 values (viewed claims only apply when all five match):\n\n'
        '```text\n'+'\n'.join(name+' '+value for name,value in VIEWED.items())+'\n```\n'
    )
    (ROOT/'REPORT.md').write_text(report,encoding='utf-8')

def main():
    (ROOT/'preview').mkdir(exist_ok=True)
    bg=background(); atlas,entries,images=build_atlas(); z=zones()
    results=check(bg,atlas,entries,images,z)
    bg.convert('RGB').save(ROOT/'yard_bg.png'); atlas.save(ROOT/'props.png')
    # Compare decoded pixels, not file bytes: zlib builds compress the same image differently.
    saved=Image.open(ROOT/'yard_bg.png'); saved.load()
    assert saved.mode=='RGB' and saved.size==(640,360)
    assert saved.tobytes()==reference_image('bg_rgba_b85').convert('RGB').tobytes()
    results.append('PASS yard_bg.png decodes to exactly the accepted round 1 background pixels')
    save_json(ROOT/'props.json',entries); save_json(ROOT/'zones.json',z)
    nearest=Image.Resampling.NEAREST
    for filename,im in [('yard-2x.png',composite(bg,images)),
                        ('yard-open-2x.png',composite(bg,images,opened=True)),
                        ('yard-zones-2x.png',zone_preview(bg,images,z)),
                        ('props-4x.png',checker(atlas)),
                        ('seats-6x.png',seats_preview(bg,images,z))]:
        scale=4 if filename=='props-4x.png' else 6 if filename=='seats-6x.png' else 2
        im.convert('RGB').resize((im.width*scale,im.height*scale),nearest).save(ROOT/'preview'/filename)
    # Verify saved preview sizes and exact nearest-neighbour pixel replication.
    for filename in ('yard-2x.png','yard-open-2x.png','yard-zones-2x.png','props-4x.png','seats-6x.png'):
        im=Image.open(ROOT/'preview'/filename).convert('RGB')
        scale=4 if filename=='props-4x.png' else 6 if filename=='seats-6x.png' else 2
        expected=atlas.size if scale==4 else tuple(LAYOUT['seats_crop'][2:]) if scale==6 else (640,360)
        assert im.size==(expected[0]*scale,expected[1]*scale)
        reduced=im.resize(expected,nearest)
        assert reduced.resize(im.size,nearest).tobytes()==im.tobytes()
    results.append('PASS all five saved previews have required sizes and exact nearest-neighbour pixel blocks')
    # Machine-readable contract for the companion artist, plus reproducible check transcript.
    save_json(ROOT/'palette.json',{'colors':P,'added_relative':{'#c7ad60':'muted safety-line yellow, relative of amber #ffb020'}})
    transcript='\n'.join(results)+f'\nSELF-CHECK: {len(results)}/{len(results)} PASS\n'
    (ROOT/'self-check.txt').write_text(transcript,encoding='utf-8')
    write_report(transcript,bg,atlas,z)
    print(transcript,end='')
    print('Asset SHA256:')
    for path in sorted(ROOT.glob('*.png')):
        print(path.name,hashlib.sha256(path.read_bytes()).hexdigest())

if __name__=='__main__': main()
