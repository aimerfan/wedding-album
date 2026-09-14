// screens-style-a.jsx — 風格 A：溫柔典雅 (米白、奶油、玫瑰金)
// 8 個畫面：歡迎、首頁(瀑布流)、上傳選擇、上傳編輯(寫祝福)、
//         祝福留言牆、婚紗欣賞、照片詳情、我的個人頁

const A = {
  bg: '#FAF6F0',          // 米白
  bgSoft: '#F4EBE0',      // 奶油
  bgDeep: '#EDE0CE',
  ink: '#3D2E26',         // 深棕
  inkSoft: '#7A6557',
  inkMute: '#A89484',
  rose: '#B76E79',        // 玫瑰金
  roseSoft: '#D9A9AE',
  gold: '#C9A86A',
  line: 'rgba(61,46,38,0.10)',
  card: '#FFFCF7',
  serif: '"Noto Serif TC", "Songti TC", "PingFang TC", serif',
  sans: '"Noto Sans TC", "PingFang TC", -apple-system, sans-serif',
  display: '"Cormorant Garamond", "Noto Serif TC", serif',
};

// ────────────────────────────────────────────────────────────
// 共用：佔位相片（柔和漸層 + 序號）
// ────────────────────────────────────────────────────────────
const PHOTO_GRADIENTS = [
  ['#E8D4C8', '#C9A48E'], ['#D4B8A8', '#A88876'],
  ['#EAD9C5', '#C2A179'], ['#D9C2B0', '#A88562'],
  ['#E5D0BE', '#B8967A'], ['#DBC5B2', '#9C7E68'],
  ['#EFDFC9', '#C49E7C'], ['#E0CAB8', '#A8836A'],
  ['#E8D8C5', '#BC9778'], ['#D6BCA9', '#9D7B62'],
];

function PhotoTile({ idx = 0, ratio = '4/5', label, children, style = {} }) {
  const [a, b] = PHOTO_GRADIENTS[idx % PHOTO_GRADIENTS.length];
  return (
    <div style={{
      width: '100%', aspectRatio: ratio, position: 'relative', overflow: 'hidden',
      background: `linear-gradient(135deg, ${a} 0%, ${b} 100%)`,
      ...style,
    }}>
      {/* 微紋理 */}
      <div style={{
        position: 'absolute', inset: 0, opacity: 0.25,
        backgroundImage: `repeating-linear-gradient(45deg, transparent 0 14px, rgba(255,255,255,0.08) 14px 15px)`,
      }} />
      {label && (
        <div style={{
          position: 'absolute', bottom: 8, left: 10, fontSize: 9,
          fontFamily: 'ui-monospace, "SF Mono", monospace',
          color: 'rgba(255,255,255,0.7)', letterSpacing: 0.5,
        }}>{label}</div>
      )}
      {children}
    </div>
  );
}

// 細線分隔（裝飾性，內含小菱形）
function DecoDivider({ color = A.gold, width = 80 }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8 }}>
      <div style={{ width, height: 1, background: color, opacity: 0.5 }} />
      <svg width="6" height="6" viewBox="0 0 6 6"><path d="M3 0L6 3L3 6L0 3Z" fill={color} /></svg>
      <div style={{ width, height: 1, background: color, opacity: 0.5 }} />
    </div>
  );
}

// 底部 Tab Bar — 5 項目 (iOS spec: 49pt content + 34pt safe area = 83pt total)
function TabBar({ active = 'feed' }) {
  const tabs = [
    { id: 'feed', label: '相簿', nav: 'feed', icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
        <rect x="3" y="3" width="18" height="18" rx="2.5"/>
        <circle cx="9" cy="9" r="1.5"/>
        <path d="M21 16l-5-5L5 21"/>
      </svg>
    )},
    { id: 'upload', label: '上傳', nav: 'upload1', icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 4v14M5 11l7-7 7 7"/>
        <path d="M4 21h16"/>
      </svg>
    )},
    { id: 'wedding', label: '婚紗集', nav: 'wedding', icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 21s-7-5-7-11a4 4 0 017-2.5A4 4 0 0119 10c0 6-7 11-7 11z"/>
      </svg>
    )},
    { id: 'saved', label: '收藏', nav: 'blessings', icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
        <path d="M19 21l-7-5-7 5V5a2 2 0 012-2h10a2 2 0 012 2z"/>
      </svg>
    )},
    { id: 'me', label: '我的', nav: 'me', icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="8" r="4"/>
        <path d="M4 21c1.5-4 4.5-6 8-6s6.5 2 8 6"/>
      </svg>
    )},
  ];
  const onTabClick = (navKey) => { if (window.__navTo) window.__navTo(navKey); };
  return (
    <div style={{
      position: 'absolute', bottom: 0, left: 0, right: 0,
      height: 83,
      background: 'rgba(255,252,247,0.95)',
      backdropFilter: 'blur(20px)',
      WebkitBackdropFilter: 'blur(20px)',
      borderTop: '0.5px solid rgba(61,46,38,0.18)',
      paddingBottom: 34, paddingTop: 10,
      display: 'flex', justifyContent: 'space-around',
      alignItems: 'flex-start',
      zIndex: 30,
      boxSizing: 'border-box',
    }}>
      {tabs.map(t => (
        <div key={t.id} onClick={() => onTabClick(t.nav)} style={{
          display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 3,
          color: t.id === active ? A.rose : A.inkMute,
          fontFamily: A.sans, fontSize: 9, cursor: 'pointer',
          minWidth: 40,
        }}>
          {t.icon}
          <span style={{ letterSpacing: 0.3 }}>{t.label}</span>
        </div>
      ))}
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// 1. 歡迎 / 輸入暱稱頁
// ════════════════════════════════════════════════════════════
function ScreenWelcome() {
  const nav = (k) => (window.__navTo || (()=>{}))(k);
  return (
    <div style={{
      width: '100%', height: '100%', background: A.bg,
      fontFamily: A.sans, color: A.ink, position: 'relative',
      overflow: 'hidden',
    }}>
      {/* 上方裝飾相片 */}
      <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: 380, overflow: 'hidden' }}>
        <PhotoTile idx={0} ratio="auto" style={{ height: 380 }} />
        <div style={{
          position: 'absolute', inset: 0,
          background: `linear-gradient(180deg, transparent 0%, transparent 50%, ${A.bg} 100%)`,
        }} />
      </div>

      {/* 頂部小字 */}
      <div style={{
        position: 'absolute', top: 70, left: 0, right: 0,
        textAlign: 'center', color: '#fff',
        fontFamily: A.display, fontStyle: 'italic',
        fontSize: 13, letterSpacing: 4,
      }}>OUR WEDDING · 2026</div>

      {/* 主要內容 */}
      <div style={{
        position: 'absolute', top: 280, left: 28, right: 28,
        display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 14,
      }}>
        <div style={{
          fontFamily: A.serif, fontSize: 30, fontWeight: 500,
          letterSpacing: 1, color: A.ink, lineHeight: 1.1,
          whiteSpace: 'nowrap',
        }}>俊鴻 <span style={{ fontFamily: A.display, fontStyle: 'italic', color: A.rose, margin: '0 4px' }}>&</span> 鈺婷</div>

        <DecoDivider />

        <div style={{
          fontFamily: A.display, fontStyle: 'italic',
          fontSize: 15, letterSpacing: 3, color: A.inkSoft,
        }}>2026 · 10 · 17</div>

        <div style={{
          marginTop: 32, fontSize: 13, color: A.inkSoft,
          textAlign: 'center', lineHeight: 1.8, padding: '0 16px',
        }}>
          歡迎你來到我們的婚禮<br/>
          請留下你的名字<br/>
          一起記錄這個值得收藏的日子
        </div>

        {/* 名稱輸入 */}
        <div style={{
          marginTop: 28, width: '100%',
          background: A.card, borderRadius: 14,
          border: `1px solid ${A.line}`,
          padding: '18px 20px',
          display: 'flex', flexDirection: 'column', gap: 6,
        }}>
          <div style={{ fontSize: 11, color: A.inkMute, letterSpacing: 1.5 }}>你的名字</div>
          <div style={{
            fontFamily: A.serif, fontSize: 18, color: A.ink,
            display: 'flex', alignItems: 'center', gap: 4,
          }}>
            <span>小慧</span>
            <span style={{
              display: 'inline-block', width: 1.5, height: 18,
              background: A.rose, marginLeft: 2,
              animation: 'blink 1s infinite',
            }} />
          </div>
        </div>

        {/* 開始按鈕 */}
        <button style={{
          marginTop: 20, width: '100%', height: 52,
          background: A.rose, color: '#fff', border: 'none',
          borderRadius: 26, fontFamily: A.sans, fontSize: 15,
          letterSpacing: 4, fontWeight: 500,
          boxShadow: `0 8px 24px ${A.rose}40`,
        }}
        onClick={() => nav('feed')}>進 入 相 簿</button>

        <div style={{ marginTop: 12, fontSize: 11, color: A.inkMute, letterSpacing: 1 }}>
          進入後即代表同意分享你拍攝的回憶
        </div>
      </div>
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// 2. 首頁 — 瀑布流 (Pinterest 風)
// ════════════════════════════════════════════════════════════
function ScreenFeed() {
  const nav = (k) => (window.__navTo || (()=>{}))(k);
  const photos = [
    { i: 0, ratio: '3/4', name: '小慧' },
    { i: 1, ratio: '4/5', name: '阿凱' },
    { i: 2, ratio: '1/1', name: '婷婷' },
    { i: 3, ratio: '4/3', name: '志明' },
    { i: 4, ratio: '3/4', name: '美玲', video: true },
    { i: 5, ratio: '4/5', name: '建宏' },
    { i: 6, ratio: '1/1', name: '佳穎' },
    { i: 7, ratio: '3/4', name: '俊豪' },
  ];
  // 兩欄分配
  const colA = photos.filter((_, i) => i % 2 === 0);
  const colB = photos.filter((_, i) => i % 2 === 1);

  const Card = ({ p }) => (
    <div style={{
      borderRadius: 12, overflow: 'hidden', position: 'relative',
      background: A.card, boxShadow: '0 1px 3px rgba(61,46,38,0.06)',
    }}>
      <PhotoTile idx={p.i} ratio={p.ratio}>
        {p.video && (
          <div style={{
            position: 'absolute', top: 8, right: 8,
            background: 'rgba(0,0,0,0.5)', borderRadius: 12,
            padding: '3px 8px', display: 'flex', alignItems: 'center', gap: 4,
            fontSize: 9, color: '#fff', fontFamily: A.sans,
          }}>
            <svg width="9" height="9" viewBox="0 0 12 12" fill="#fff"><path d="M3 2v8l7-4z"/></svg>
            0:24
          </div>
        )}
      </PhotoTile>
      <div style={{ padding: '8px 10px', fontSize: 11, color: A.inkSoft, fontFamily: A.sans, display: 'flex', alignItems: 'center', gap: 6 }}>
        <div style={{ width: 16, height: 16, borderRadius: 8, background: A.bgDeep, color: A.ink, fontSize: 9, display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: A.serif }}>{p.name[0]}</div>
        {p.name}
      </div>
    </div>
  );

  return (
    <div style={{
      width: '100%', height: '100%', background: A.bg,
      fontFamily: A.sans, color: A.ink, position: 'relative',
      overflow: 'hidden', paddingBottom: 83, boxSizing: 'border-box',
    }}>
      {/* 頂部 */}
      <div style={{ paddingTop: 56, paddingLeft: 20, paddingRight: 20, paddingBottom: 16 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <div style={{ fontFamily: A.display, fontStyle: 'italic', fontSize: 12, color: A.gold, letterSpacing: 3 }}>OCT · 17 · 2026</div>
            <div style={{ fontFamily: A.serif, fontSize: 26, fontWeight: 500, color: A.ink, marginTop: 4, letterSpacing: 1 }}>
              俊鴻 <span style={{ color: A.rose, fontFamily: A.display, fontStyle: 'italic' }}>&</span> 鈺婷
            </div>
            <div style={{ fontSize: 11, color: A.inkMute, marginTop: 4, letterSpacing: 1 }}>共 247 張回憶 · 32 位賓客</div>
          </div>
          <div style={{
            width: 36, height: 36, borderRadius: 18,
            background: A.card, border: `1px solid ${A.line}`,
            display: 'flex', alignItems: 'center', justifyContent: 'center', color: A.ink,
          }}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round">
              <circle cx="11" cy="11" r="7"/><path d="M16 16l5 5"/>
            </svg>
          </div>
        </div>

        {/* 篩選 chips */}
        <div style={{ marginTop: 18, display: 'flex', gap: 8, overflowX: 'auto' }}>
          {[
            { l: '全部', active: true },
            { l: '今天' },
            { l: '迎賓' },
            { l: '儀式' },
            { l: '宴客' },
            { l: '影片' },
          ].map((c, i) => (
            <div key={i} style={{
              padding: '6px 14px', borderRadius: 14,
              background: c.active ? A.ink : 'transparent',
              color: c.active ? A.bg : A.inkSoft,
              fontSize: 11, letterSpacing: 1, whiteSpace: 'nowrap',
              border: c.active ? 'none' : `1px solid ${A.line}`,
            }}>{c.l}</div>
          ))}
        </div>
      </div>

      {/* 瀑布流 */}
      <div style={{ padding: '0 16px', display: 'flex', gap: 10 }}>
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 10 }}>
          {colA.map(p => <Card key={p.i} p={p} />)}
        </div>
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 10 }}>
          {colB.map(p => <Card key={p.i} p={p} />)}
        </div>
      </div>

      <div onClick={() => nav('detail')} style={{ position:'absolute', top:200, left:16, right:16, bottom:90, cursor:'pointer' }} />
      <div style={{ position:'absolute', bottom:0, left:0, right:0, display:'flex', zIndex:35, paddingBottom:22, paddingTop:10, pointerEvents:'none' }}>
        <div onClick={() => nav('feed')} style={{ flex:1, height:83, pointerEvents:'auto', cursor:'pointer' }} />
        <div onClick={() => nav('upload1')} style={{ flex:1, height:83, pointerEvents:'auto', cursor:'pointer' }} />
        <div onClick={() => nav('wedding')} style={{ flex:1, height:83, pointerEvents:'auto', cursor:'pointer' }} />
        <div onClick={() => nav('blessings')} style={{ flex:1, height:83, pointerEvents:'auto', cursor:'pointer' }} />
        <div onClick={() => nav('me')} style={{ flex:1, height:83, pointerEvents:'auto', cursor:'pointer' }} />
      </div>
      <TabBar active="feed" />
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// 3. 上傳流程 - 選擇照片
// ════════════════════════════════════════════════════════════
function ScreenUploadPicker() {
  const nav = (k) => (window.__navTo || (()=>{}))(k);
  const items = Array.from({ length: 12 }, (_, i) => ({
    i, selected: [1, 4, 5, 8].includes(i),
    selectedOrder: { 1: 1, 4: 2, 5: 3, 8: 4 }[i],
    video: i === 4,
  }));

  return (
    <div style={{
      width: '100%', height: '100%', background: A.bg,
      fontFamily: A.sans, color: A.ink, position: 'relative',
      overflow: 'hidden',
    }}>
      {/* 頂部 */}
      <div style={{
        position: 'relative', zIndex: 5,
        paddingTop: 56, paddingLeft: 16, paddingRight: 16, paddingBottom: 12,
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        borderBottom: `1px solid ${A.line}`,
      }}>
        <div style={{ fontSize: 14, color: A.inkSoft }}>取消</div>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontFamily: A.serif, fontSize: 16, fontWeight: 500, color: A.ink }}>選擇照片</div>
          <div style={{ fontSize: 10, color: A.inkMute, marginTop: 1, letterSpacing: 1 }}>已選 4 / 30</div>
        </div>
        <div style={{
          fontSize: 13, color: A.rose, fontWeight: 500,
        }} onClick={() => nav('upload2')}>下一步</div>
      </div>

      {/* 來源切換 */}
      <div style={{ display: 'flex', gap: 6, padding: '14px 16px' }}>
        {[
          { l: '相機膠捲', active: true },
          { l: '婚禮當天' },
          { l: '影片' },
        ].map((s, i) => (
          <div key={i} style={{
            padding: '7px 14px', borderRadius: 14, fontSize: 11, letterSpacing: 1,
            background: s.active ? A.ink : A.card,
            color: s.active ? A.bg : A.inkSoft,
            border: s.active ? 'none' : `1px solid ${A.line}`,
          }}>{s.l}</div>
        ))}
      </div>

      {/* 網格 */}
      <div style={{
        padding: '0 8px',
        display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 4,
      }}>
        {items.map(it => (
          <div key={it.i} style={{ position: 'relative' }}>
            <PhotoTile idx={it.i} ratio="1/1" />
            {/* 選擇標記 */}
            <div style={{
              position: 'absolute', top: 6, right: 6,
              width: 22, height: 22, borderRadius: 11,
              background: it.selected ? A.rose : 'rgba(255,255,255,0.4)',
              border: it.selected ? 'none' : '1.5px solid rgba(255,255,255,0.9)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              color: '#fff', fontSize: 11, fontWeight: 600,
              backdropFilter: 'blur(6px)',
            }}>{it.selectedOrder ?? ''}</div>
            {it.video && (
              <div style={{
                position: 'absolute', bottom: 6, left: 6,
                fontSize: 9, color: '#fff', display: 'flex', alignItems: 'center', gap: 3,
                background: 'rgba(0,0,0,0.4)', borderRadius: 8, padding: '2px 6px',
              }}>
                <svg width="8" height="8" viewBox="0 0 12 12" fill="#fff"><path d="M3 2v8l7-4z"/></svg>
                0:18
              </div>
            )}
          </div>
        ))}
      </div>

      {/* 底部選中浮層 */}
      <div style={{
        position: 'absolute', bottom: 24, left: 16, right: 16,
        background: A.ink, borderRadius: 28,
        padding: '10px 12px 10px 16px',
        display: 'flex', alignItems: 'center', gap: 10,
        boxShadow: '0 12px 32px rgba(61,46,38,0.25)',
      }}>
        <div style={{ display: 'flex' }}>
          {[1,4,5,8].map((id, i) => (
            <div key={id} style={{
              width: 28, height: 28, borderRadius: 14, overflow: 'hidden',
              border: `1.5px solid ${A.ink}`, marginLeft: i === 0 ? 0 : -8,
            }}>
              <PhotoTile idx={id} ratio="1/1" />
            </div>
          ))}
        </div>
        <div style={{ flex: 1, color: A.bg, fontSize: 12, letterSpacing: 1 }}>
          已選 <span style={{ color: A.roseSoft, fontWeight: 600, margin: '0 2px' }}>4</span> 個項目
        </div>
        <div style={{
          padding: '7px 14px', background: A.rose, color: '#fff',
          borderRadius: 16, fontSize: 12, letterSpacing: 1,
        }} onClick={() => nav('upload2')}>下一步 →</div>
      </div>
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// 4. 上傳編輯 — 寫祝福語
// ════════════════════════════════════════════════════════════
function ScreenUploadEdit() {
  const nav = (k) => (window.__navTo || (()=>{}))(k);
  return (
    <div style={{
      width: '100%', height: '100%', background: A.bg,
      fontFamily: A.sans, color: A.ink, position: 'relative',
      overflow: 'hidden',
    }}>
      {/* 頂部 */}
      <div style={{
        paddingTop: 56, paddingLeft: 16, paddingRight: 16, paddingBottom: 12,
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        borderBottom: `1px solid ${A.line}`,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 14, color: A.inkSoft }}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"><path d="M15 6l-6 6 6 6"/></svg>
          返回
        </div>
        <div style={{ fontFamily: A.serif, fontSize: 16, fontWeight: 500 }}>留下祝福</div>
        <div style={{ fontSize: 13, color: A.inkMute }}>跳過</div>
      </div>

      {/* 已選照片預覽 (橫向滑動) */}
      <div style={{ padding: '18px 16px 14px' }}>
        <div style={{ fontSize: 11, color: A.inkMute, letterSpacing: 1.5, marginBottom: 8 }}>4 個項目 · 將公開分享</div>
        <div style={{ display: 'flex', gap: 8 }}>
          {[1, 4, 5, 8].map((id, i) => (
            <div key={id} style={{
              width: 64, height: 80, borderRadius: 8, overflow: 'hidden',
              flexShrink: 0, position: 'relative',
              border: `1px solid ${A.line}`,
            }}>
              <PhotoTile idx={id} ratio="auto" style={{ height: '100%' }} />
              {i === 1 && (
                <div style={{
                  position: 'absolute', bottom: 4, right: 4,
                  background: 'rgba(0,0,0,0.5)', borderRadius: 6,
                  padding: '1px 4px', fontSize: 8, color: '#fff',
                }}>影片</div>
              )}
            </div>
          ))}
          <div style={{
            width: 64, height: 80, borderRadius: 8, flexShrink: 0,
            border: `1.5px dashed ${A.inkMute}`,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            color: A.inkMute, fontSize: 22, fontWeight: 300,
          }}>+</div>
        </div>
      </div>

      {/* 暱稱 */}
      <div style={{ padding: '0 16px', marginBottom: 14 }}>
        <div style={{
          background: A.card, borderRadius: 12,
          border: `1px solid ${A.line}`,
          padding: '10px 14px',
          display: 'flex', alignItems: 'center', gap: 10,
        }}>
          <div style={{
            width: 30, height: 30, borderRadius: 15, background: A.bgSoft,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontFamily: A.serif, fontSize: 13, color: A.ink,
          }}>慧</div>
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: 10, color: A.inkMute, letterSpacing: 1 }}>以此暱稱發布</div>
            <div style={{ fontSize: 14, color: A.ink, marginTop: 1 }}>小慧</div>
          </div>
          <div style={{ fontSize: 11, color: A.rose }}>更改</div>
        </div>
      </div>

      {/* 祝福語輸入 */}
      <div style={{ padding: '0 16px' }}>
        <div style={{
          background: A.card, borderRadius: 12,
          border: `1px solid ${A.line}`,
          padding: '14px 16px',
          minHeight: 140, display: 'flex', flexDirection: 'column', gap: 10,
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill={A.rose}>
              <path d="M12 21s-7-5-7-11a4 4 0 017-2.5A4 4 0 0119 10c0 6-7 11-7 11z"/>
            </svg>
            <div style={{ fontSize: 11, color: A.rose, letterSpacing: 1 }}>寫下你的祝福（選填）</div>
          </div>

          <div style={{
            fontFamily: A.serif, fontSize: 15, color: A.ink, lineHeight: 1.7,
            flex: 1,
          }}>
            願你們的愛情<br/>
            如同今日的天氣<br/>
            晴朗、明亮、永遠溫暖<span style={{
              display: 'inline-block', width: 1.5, height: 16, background: A.rose,
              verticalAlign: -2, marginLeft: 2,
              animation: 'blink 1s infinite',
            }} />
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderTop: `1px solid ${A.line}`, paddingTop: 8 }}>
            <div style={{ display: 'flex', gap: 12, color: A.inkMute }}>
              <span style={{ fontSize: 14 }}>♥</span>
              <span style={{ fontSize: 14 }}>♡</span>
              <span style={{ fontSize: 14 }}>✿</span>
            </div>
            <div style={{ fontSize: 10, color: A.inkMute }}>43 / 200</div>
          </div>
        </div>

        {/* 設定 */}
        <div style={{ marginTop: 14, background: A.card, borderRadius: 12, border: `1px solid ${A.line}`, overflow: 'hidden' }}>
          {[
            { l: '允許其他賓客看到', toggle: true, on: true },
            { l: '附加位置：婚宴會館 3F', toggle: true, on: false, last: true },
          ].map((r, i) => (
            <div key={i} style={{
              padding: '12px 16px', display: 'flex', alignItems: 'center', justifyContent: 'space-between',
              borderBottom: r.last ? 'none' : `1px solid ${A.line}`,
              fontSize: 13, color: A.ink,
            }}>
              <span>{r.l}</span>
              <div style={{
                width: 36, height: 22, borderRadius: 11,
                background: r.on ? A.rose : A.bgDeep,
                position: 'relative',
              }}>
                <div style={{
                  position: 'absolute', top: 2, left: r.on ? 16 : 2,
                  width: 18, height: 18, borderRadius: 9, background: '#fff',
                  boxShadow: '0 1px 3px rgba(0,0,0,0.2)', transition: 'left 0.2s',
                }}/>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 底部上傳按鈕 */}
      <div style={{
        position: 'absolute', bottom: 0, left: 0, right: 0,
        padding: '12px 16px 28px', background: `linear-gradient(180deg, transparent, ${A.bg} 30%)`,
      }}>
        <button style={{
          width: '100%', height: 50, borderRadius: 25, border: 'none',
          background: A.rose, color: '#fff', fontSize: 14, letterSpacing: 4,
          fontFamily: A.sans, fontWeight: 500,
          boxShadow: `0 8px 20px ${A.rose}40`,
        }}
        onClick={() => nav('feed')}>上 傳 4 個 項 目</button>
      </div>
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// 5. 祝福留言牆
// ════════════════════════════════════════════════════════════
function ScreenBlessings() {
  const nav = (k) => (window.__navTo || (()=>{}))(k);
  const blessings = [
    { name: '阿凱', initial: '凱', text: '俊鴻是我大學最好的兄弟，一路看著他追到鈺婷。今天看到你們穿上禮服，眼淚差點掉下來。祝你們白頭偕老！', time: '剛剛', color: A.bgSoft },
    { name: '美玲阿姨', initial: '玲', text: '從小看著婷婷長大，今天看到她當新娘真的好美。願你們的婚姻甜甜蜜蜜，早生貴子。', time: '12 分鐘前', color: A.bgDeep },
    { name: '志明', initial: '明', text: '恭喜恭喜！', time: '38 分鐘前', color: A.bgSoft },
    { name: '佳穎', initial: '穎', text: '兩個人在一起的樣子真好看。 ♥', time: '1 小時前', color: A.bgDeep },
  ];

  return (
    <div style={{
      width: '100%', height: '100%', background: A.bg,
      fontFamily: A.sans, color: A.ink, position: 'relative',
      overflow: 'hidden', paddingBottom: 83, boxSizing: 'border-box',
    }}>
      {/* 頂部 */}
      <div style={{ paddingTop: 56, paddingLeft: 20, paddingRight: 20, paddingBottom: 14 }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ fontSize: 14, color: A.inkSoft }}>← 相簿</div>
          <div style={{ fontSize: 12, color: A.gold, letterSpacing: 2 }}>BLESSINGS</div>
          <div style={{ width: 30 }}/>
        </div>
        <div style={{ marginTop: 16, textAlign: 'center' }}>
          <div style={{ fontFamily: A.serif, fontSize: 24, fontWeight: 500, color: A.ink, letterSpacing: 1 }}>祝 福 留 言</div>
          <DecoDivider color={A.gold} width={40} />
          <div style={{ fontSize: 11, color: A.inkMute, marginTop: 8, letterSpacing: 1 }}>32 位賓客留下了 47 則祝福</div>
        </div>
      </div>

      {/* 留言列表 */}
      <div style={{ padding: '8px 16px', display: 'flex', flexDirection: 'column', gap: 10 }}>
        {blessings.map((b, i) => (
          <div key={i} style={{
            background: b.color, borderRadius: 14,
            padding: '14px 16px',
            position: 'relative',
            transform: i % 2 === 0 ? 'rotate(-0.4deg)' : 'rotate(0.4deg)',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
              <div style={{
                width: 28, height: 28, borderRadius: 14, background: A.card,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontFamily: A.serif, fontSize: 13, color: A.ink,
                border: `1px solid ${A.line}`,
              }}>{b.initial}</div>
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: 13, color: A.ink, fontWeight: 500 }}>{b.name}</div>
                <div style={{ fontSize: 10, color: A.inkMute, letterSpacing: 0.5 }}>{b.time}</div>
              </div>
              <svg width="14" height="14" viewBox="0 0 24 24" fill={A.rose} opacity="0.6">
                <path d="M12 21s-7-5-7-11a4 4 0 017-2.5A4 4 0 0119 10c0 6-7 11-7 11z"/>
              </svg>
            </div>
            <div style={{
              fontFamily: A.serif, fontSize: 14, color: A.ink, lineHeight: 1.7,
              textAlign: 'justify',
            }}>{b.text}</div>
          </div>
        ))}
      </div>

      {/* 寫祝福浮動按鈕 */}
      <div style={{
        position: 'absolute', bottom: 100, right: 20,
        background: A.ink, color: '#fff',
        padding: '12px 18px', borderRadius: 24,
        display: 'flex', alignItems: 'center', gap: 6,
        fontSize: 12, letterSpacing: 1,
        boxShadow: '0 8px 20px rgba(61,46,38,0.3)',
      }}>
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="1.8" strokeLinecap="round"><path d="M12 19l7-7 3 3-7 7-3-3z"/><path d="M18 13l-1.5-7.5L2 2l3.5 14.5L13 18l5-5z"/></svg>
        寫祝福
      </div>

      <div style={{ position:'absolute', bottom:0, left:0, right:0, display:'flex', zIndex:35, paddingBottom:22, paddingTop:10, pointerEvents:'none' }}>
        <div onClick={() => nav('feed')} style={{ flex:1, height:83, pointerEvents:'auto', cursor:'pointer' }} />
        <div onClick={() => nav('upload1')} style={{ flex:1, height:83, pointerEvents:'auto', cursor:'pointer' }} />
        <div onClick={() => nav('wedding')} style={{ flex:1, height:83, pointerEvents:'auto', cursor:'pointer' }} />
        <div onClick={() => nav('blessings')} style={{ flex:1, height:83, pointerEvents:'auto', cursor:'pointer' }} />
        <div onClick={() => nav('me')} style={{ flex:1, height:83, pointerEvents:'auto', cursor:'pointer' }} />
      </div>
      <TabBar active="feed" />
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// 6. 婚紗欣賞區
// ════════════════════════════════════════════════════════════
function ScreenWedding() {
  const nav = (k) => (window.__navTo || (()=>{}))(k);
  return (
    <div style={{
      width: '100%', height: '100%', background: A.ink,
      fontFamily: A.sans, color: '#fff', position: 'relative',
      overflow: 'hidden', paddingBottom: 83, boxSizing: 'border-box',
    }}>
      {/* 頂部 hero */}
      <div style={{ position: 'relative' }}>
        <PhotoTile idx={2} ratio="auto" style={{ height: 380 }} />
        <div style={{
          position: 'absolute', inset: 0,
          background: 'linear-gradient(180deg, rgba(0,0,0,0.4) 0%, transparent 30%, transparent 60%, rgba(61,46,38,0.95) 100%)',
        }} />

        {/* 頂部標題列 */}
        <div style={{ position: 'absolute', top: 56, left: 20, right: 20, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ fontSize: 14, opacity: 0.9 }}>← 相簿</div>
          <div style={{
            background: 'rgba(255,255,255,0.15)', backdropFilter: 'blur(8px)',
            padding: '4px 10px', borderRadius: 10,
            fontSize: 9, letterSpacing: 1.5,
          }}>僅供觀賞 · 無法下載</div>
        </div>

        {/* 文字 */}
        <div style={{ position: 'absolute', bottom: 32, left: 20, right: 20 }}>
          <div style={{ fontFamily: A.display, fontStyle: 'italic', fontSize: 12, color: A.gold, letterSpacing: 4 }}>OUR PRE-WEDDING</div>
          <div style={{ fontFamily: A.serif, fontSize: 30, fontWeight: 500, marginTop: 6, letterSpacing: 2 }}>婚 紗 集</div>
          <div style={{ fontSize: 11, opacity: 0.7, marginTop: 6, letterSpacing: 1 }}>陽明山 · 2026 春末 · 共 24 張</div>
        </div>
      </div>

      {/* 集合切換 */}
      <div style={{ padding: '20px 16px 12px', display: 'flex', gap: 8, overflowX: 'auto' }}>
        {[
          { l: '陽明山外景', active: true },
          { l: '棚拍經典' },
          { l: '海邊夕陽' },
        ].map((c, i) => (
          <div key={i} style={{
            padding: '7px 14px', borderRadius: 14, fontSize: 11, letterSpacing: 1, whiteSpace: 'nowrap',
            background: c.active ? '#fff' : 'transparent',
            color: c.active ? A.ink : 'rgba(255,255,255,0.7)',
            border: c.active ? 'none' : '1px solid rgba(255,255,255,0.2)',
          }}>{c.l}</div>
        ))}
      </div>

      {/* 雜誌式排版 */}
      <div style={{ padding: '0 16px', display: 'flex', flexDirection: 'column', gap: 8 }}>
        {/* 大圖 */}
        <div style={{ borderRadius: 8, overflow: 'hidden', position: 'relative' }}>
          <PhotoTile idx={3} ratio="3/2" />
          <div style={{ position: 'absolute', bottom: 10, right: 12, fontFamily: A.display, fontStyle: 'italic', fontSize: 14, color: '#fff', textShadow: '0 1px 4px rgba(0,0,0,0.6)' }}>
            01 · Hill Path
          </div>
        </div>
        {/* 兩格 */}
        <div style={{ display: 'flex', gap: 8 }}>
          <div style={{ flex: 1, borderRadius: 8, overflow: 'hidden' }}>
            <PhotoTile idx={5} ratio="3/4" label="02 · Wildflowers" />
          </div>
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 8 }}>
            <div style={{ borderRadius: 8, overflow: 'hidden' }}>
              <PhotoTile idx={6} ratio="1/1" label="03" />
            </div>
            <div style={{ borderRadius: 8, overflow: 'hidden' }}>
              <PhotoTile idx={7} ratio="1/1" label="04" />
            </div>
          </div>
        </div>
      </div>

      <div style={{ position:'absolute', bottom:0, left:0, right:0, display:'flex', zIndex:35, paddingBottom:22, paddingTop:10, pointerEvents:'none' }}>
        <div onClick={() => nav('feed')} style={{ flex:1, height:83, pointerEvents:'auto', cursor:'pointer' }} />
        <div onClick={() => nav('upload1')} style={{ flex:1, height:83, pointerEvents:'auto', cursor:'pointer' }} />
        <div onClick={() => nav('wedding')} style={{ flex:1, height:83, pointerEvents:'auto', cursor:'pointer' }} />
        <div onClick={() => nav('blessings')} style={{ flex:1, height:83, pointerEvents:'auto', cursor:'pointer' }} />
        <div onClick={() => nav('me')} style={{ flex:1, height:83, pointerEvents:'auto', cursor:'pointer' }} />
      </div>
      <TabBar active="wedding" />
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// 7. 單張照片詳情頁 (含祝福語)
// ════════════════════════════════════════════════════════════
function ScreenPhotoDetail() {
  const nav = (k) => (window.__navTo || (()=>{}))(k);
  return (
    <div style={{
      width: '100%', height: '100%', background: A.ink,
      fontFamily: A.sans, color: '#fff', position: 'relative',
      overflow: 'hidden',
    }}>
      {/* 頂部關閉 */}
      <div style={{
        position: 'absolute', top: 56, left: 16, right: 16, zIndex: 10,
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      }}>
        <div style={{
          width: 32, height: 32, borderRadius: 16,
          background: 'rgba(255,255,255,0.15)', backdropFilter: 'blur(8px)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2" onClick={() => nav('feed')} style={{cursor:'pointer'}}><path d="M18 6L6 18M6 6l12 12"/></svg>
        </div>
        <div style={{ fontSize: 11, letterSpacing: 1 }}>3 / 247</div>
        <div style={{
          width: 32, height: 32, borderRadius: 16,
          background: 'rgba(255,255,255,0.15)', backdropFilter: 'blur(8px)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="1.8" strokeLinecap="round"><circle cx="5" cy="12" r="2"/><circle cx="12" cy="12" r="2"/><circle cx="19" cy="12" r="2"/></svg>
        </div>
      </div>

      {/* 照片 */}
      <div style={{ paddingTop: 100 }}>
        <PhotoTile idx={1} ratio="4/5" />
      </div>

      {/* 底部資訊面板 */}
      <div style={{
        position: 'absolute', bottom: 0, left: 0, right: 0,
        background: A.bg, color: A.ink,
        borderTopLeftRadius: 24, borderTopRightRadius: 24,
        padding: '20px 20px 32px',
      }}>
        {/* 拖曳條 */}
        <div style={{
          width: 36, height: 4, borderRadius: 2, background: A.line,
          margin: '0 auto 16px',
        }}/>

        {/* 上傳者 */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 14 }}>
          <div style={{
            width: 36, height: 36, borderRadius: 18, background: A.bgSoft,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontFamily: A.serif, fontSize: 15, color: A.ink,
          }}>凱</div>
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: 14, fontWeight: 500, color: A.ink }}>阿凱</div>
            <div style={{ fontSize: 10, color: A.inkMute, marginTop: 1, letterSpacing: 0.5 }}>10/17 · 18:42 · 婚宴會館</div>
          </div>
          <svg width="18" height="18" viewBox="0 0 24 24" fill={A.rose}>
            <path d="M12 21s-7-5-7-11a4 4 0 017-2.5A4 4 0 0119 10c0 6-7 11-7 11z"/>
          </svg>
          <span style={{ fontSize: 12, color: A.ink }}>12</span>
        </div>

        {/* 祝福語卡片 */}
        <div style={{
          background: A.bgSoft, borderRadius: 12, padding: '14px 16px',
          position: 'relative',
        }}>
          <div style={{
            position: 'absolute', top: -8, left: 16,
            background: A.bgSoft, padding: '0 8px',
            fontSize: 10, color: A.rose, letterSpacing: 1.5,
          }}>來自阿凱的祝福</div>
          <div style={{
            fontFamily: A.serif, fontSize: 14, color: A.ink, lineHeight: 1.7,
            textAlign: 'justify',
          }}>
            俊鴻是我大學最好的兄弟，一路看著他追到鈺婷。今天看到你們穿上禮服，眼淚差點掉下來。祝你們白頭偕老！
          </div>
        </div>
      </div>
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// 8. 我的個人頁
// ════════════════════════════════════════════════════════════
function ScreenMe() {
  const nav = (k) => (window.__navTo || (()=>{}))(k);
  const myPhotos = [0, 3, 6, 9, 2, 5];

  return (
    <div style={{
      width: '100%', height: '100%', background: A.bg,
      fontFamily: A.sans, color: A.ink, position: 'relative',
      overflow: 'hidden', paddingBottom: 83, boxSizing: 'border-box',
    }}>
      {/* 頂部背景 */}
      <div style={{
        position: 'absolute', top: 0, left: 0, right: 0, height: 200,
        background: `linear-gradient(180deg, ${A.bgSoft} 0%, ${A.bg} 100%)`,
      }} />

      {/* 頂部右側 - QR Code 按鈕 */}
      <div style={{
        position: 'absolute', top: 60, right: 20, zIndex: 5,
        width: 36, height: 36, borderRadius: 18,
        background: A.card, border: `1px solid ${A.line}`,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
      }}>
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke={A.ink} strokeWidth="1.6">
          <rect x="3" y="3" width="7" height="7" rx="1"/>
          <rect x="14" y="3" width="7" height="7" rx="1"/>
          <rect x="3" y="14" width="7" height="7" rx="1"/>
          <path d="M14 14h3v3M21 14v3M14 21h3M21 18v3"/>
        </svg>
      </div>

      {/* 個人資訊 */}
      <div style={{ paddingTop: 80, textAlign: 'center', position: 'relative' }}>
        <div style={{
          width: 76, height: 76, borderRadius: 38, margin: '0 auto',
          background: A.card, border: `2px solid ${A.bg}`,
          boxShadow: '0 4px 14px rgba(61,46,38,0.08)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontFamily: A.serif, fontSize: 32, color: A.ink,
        }}>慧</div>

        <div style={{ marginTop: 12, fontFamily: A.serif, fontSize: 20, fontWeight: 500, color: A.ink, letterSpacing: 1 }}>小慧</div>
        <div style={{ marginTop: 2, fontSize: 11, color: A.inkMute, letterSpacing: 1 }}>新娘的大學同學</div>

        {/* 統計 */}
        <div style={{
          marginTop: 18, marginLeft: 20, marginRight: 20,
          background: A.card, borderRadius: 14,
          border: `1px solid ${A.line}`,
          padding: '14px 0',
          display: 'flex', justifyContent: 'space-around',
        }}>
          {[
            { n: '12', l: '已上傳' },
            { n: '8', l: '收藏' },
            { n: '24', l: '收到的讚' },
          ].map((s, i) => (
            <React.Fragment key={i}>
              {i > 0 && <div style={{ width: 1, background: A.line }}/>}
              <div style={{ flex: 1, textAlign: 'center' }}>
                <div style={{ fontFamily: A.serif, fontSize: 22, color: A.ink, fontWeight: 500 }}>{s.n}</div>
                <div style={{ fontSize: 10, color: A.inkMute, marginTop: 2, letterSpacing: 1 }}>{s.l}</div>
              </div>
            </React.Fragment>
          ))}
        </div>
      </div>

      {/* 切換 tabs */}
      <div style={{
        marginTop: 20, padding: '0 20px',
        display: 'flex', gap: 20,
        borderBottom: `1px solid ${A.line}`,
      }}>
        {[
          { l: '我上傳的', active: true, n: 12 },
          { l: '收藏', n: 8 },
          { l: '我的祝福', n: 1 },
        ].map((t, i) => (
          <div key={i} style={{
            paddingBottom: 10, position: 'relative',
            color: t.active ? A.ink : A.inkMute,
            fontSize: 13, fontWeight: t.active ? 500 : 400,
          }}>
            {t.l} <span style={{ fontSize: 10, color: A.inkMute }}>{t.n}</span>
            {t.active && (
              <div style={{
                position: 'absolute', bottom: -1, left: 0, right: 16,
                height: 2, background: A.rose,
              }}/>
            )}
          </div>
        ))}
      </div>

      {/* 照片網格 */}
      <div style={{
        padding: '12px 16px',
        display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 4,
      }}>
        {myPhotos.map(id => (
          <div key={id} style={{ borderRadius: 6, overflow: 'hidden' }}>
            <PhotoTile idx={id} ratio="1/1" />
          </div>
        ))}
      </div>

      <div style={{ position:'absolute', bottom:0, left:0, right:0, display:'flex', zIndex:35, paddingBottom:22, paddingTop:10, pointerEvents:'none' }}>
        <div onClick={() => nav('feed')} style={{ flex:1, height:83, pointerEvents:'auto', cursor:'pointer' }} />
        <div onClick={() => nav('upload1')} style={{ flex:1, height:83, pointerEvents:'auto', cursor:'pointer' }} />
        <div onClick={() => nav('wedding')} style={{ flex:1, height:83, pointerEvents:'auto', cursor:'pointer' }} />
        <div onClick={() => nav('blessings')} style={{ flex:1, height:83, pointerEvents:'auto', cursor:'pointer' }} />
        <div onClick={() => nav('me')} style={{ flex:1, height:83, pointerEvents:'auto', cursor:'pointer' }} />
      </div>
      <TabBar active="me" />
    </div>
  );
}

Object.assign(window, {
  StyleA: { ScreenWelcome, ScreenFeed, ScreenUploadPicker, ScreenUploadEdit, ScreenBlessings, ScreenWedding, ScreenPhotoDetail, ScreenMe },
});
