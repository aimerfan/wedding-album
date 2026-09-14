
const { IOSDevice, StyleA } = window;

const SCREENS = [
  { label: '歡迎 / 輸入暱稱',    Comp: () => <StyleA.ScreenWelcome /> },
  { label: '首頁 (瀑布流)',       Comp: () => <StyleA.ScreenFeed /> },
  { label: '上傳 · 選照片',       Comp: () => <StyleA.ScreenUploadPicker /> },
  { label: '上傳 · 寫祝福',       Comp: () => <StyleA.ScreenUploadEdit /> },
  { label: '祝福留言牆',          Comp: () => <StyleA.ScreenBlessings /> },
  { label: '婚紗欣賞區',          Comp: () => <StyleA.ScreenWedding />,      dark: true },
  { label: '照片詳情 (含祝福)',   Comp: () => <StyleA.ScreenPhotoDetail />,  dark: true },
  { label: '我的個人頁',          Comp: () => <StyleA.ScreenMe /> },
];

const navMap = { welcome:0, feed:1, upload1:2, upload2:3, blessings:4, wedding:5, detail:6, me:7 };

const accent   = '#B76E79';
const bg       = '#FAF6F0';
const ink      = '#3D2E26';
const inkMute  = '#A89484';
const line     = 'rgba(61,46,38,0.10)';
const serif    = '"Noto Serif TC", serif';
const sans     = '"Noto Sans TC", sans-serif';

function InteractivePhone() {
  const [active, setActive] = React.useState(0);
  const [menuOpen, setMenuOpen] = React.useState(false);
  const cur = SCREENS[active];
  const dark = !!cur.dark;

  // 讓畫面內的 Tab / 按鈕能切換畫面
  React.useEffect(() => {
    window.__navTo = (key) => {
      const i = navMap[key];
      if (typeof i === 'number') setActive(i);
    };
  });

  const Comp = cur.Comp;

  return (
    <div style={{ position: 'relative' }}>
      {/* 手機殼 */}
      <IOSDevice width={360} height={780} dark={dark}>
        <div style={{ position: 'absolute', inset: 0 }}>
          <Comp />
        </div>
      </IOSDevice>

      {/* 工具列 */}
      <div style={{
        marginTop: 14, padding: '10px 12px',
        background: bg, borderRadius: 14, border: `1px solid ${line}`,
        display: 'flex', alignItems: 'center', gap: 8,
        fontFamily: sans,
        boxShadow: '0 4px 14px rgba(0,0,0,0.06)',
      }}>
        <button
          onClick={() => setActive((active - 1 + SCREENS.length) % SCREENS.length)}
          style={{
            width: 32, height: 32, borderRadius: 16, border: `1px solid ${line}`,
            background: '#fff', color: ink, cursor: 'pointer', flexShrink: 0,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round"><path d="M15 18l-6-6 6-6"/></svg>
        </button>

        <button
          onClick={() => setMenuOpen(!menuOpen)}
          style={{
            flex: 1, height: 32, border: 'none', borderRadius: 16,
            background: menuOpen ? accent : 'transparent',
            color: menuOpen ? '#fff' : ink,
            cursor: 'pointer',
            display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6,
            fontSize: 12, letterSpacing: 1, fontFamily: sans,
          }}>
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
            <path d="M4 6h16M4 12h16M4 18h16"/>
          </svg>
          <span style={{ fontFamily: serif, fontSize: 13 }}>{cur.label}</span>
          <span style={{ color: menuOpen ? 'rgba(255,255,255,0.7)' : inkMute, fontSize: 10, fontVariantNumeric: 'tabular-nums' }}>{active + 1}/{SCREENS.length}</span>
        </button>

        <button
          onClick={() => setActive((active + 1) % SCREENS.length)}
          style={{
            width: 32, height: 32, borderRadius: 16, border: `1px solid ${line}`,
            background: '#fff', color: ink, cursor: 'pointer', flexShrink: 0,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round"><path d="M9 18l6-6-6-6"/></svg>
        </button>
      </div>

      {/* 畫面清單 */}
      {menuOpen && (
        <div style={{
          marginTop: 8, background: bg, borderRadius: 14, border: `1px solid ${line}`,
          overflow: 'hidden', fontFamily: sans,
          boxShadow: '0 8px 24px rgba(0,0,0,0.08)',
        }}>
          {/* 畫面列表 */}
          <div style={{ padding: '8px 0' }}>
            {SCREENS.map((s, i) => (
              <div key={i} onClick={() => { setActive(i); setMenuOpen(false); }} style={{
                padding: '8px 16px', display: 'flex', alignItems: 'center', gap: 10,
                background: i === active ? '#F4EBE0' : 'transparent',
                cursor: 'pointer',
              }}>
                <div style={{
                  width: 22, fontFamily: '"Cormorant Garamond", serif', fontStyle: 'italic',
                  fontSize: 13, color: accent,
                }}>{String(i + 1).padStart(2, '0')}</div>
                <div style={{ flex: 1, fontSize: 12, color: ink, fontWeight: i === active ? 500 : 400 }}>{s.label}</div>
                {i === active && (
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke={accent} strokeWidth="2.4" strokeLinecap="round"><path d="M5 12l5 5L20 7"/></svg>
                )}
              </div>
            ))}
          </div>

        </div>
      )}
    </div>
  );
}

function App() {
  return (
    <div style={{
      minHeight: '100vh', display: 'flex', flexDirection: 'column',
      alignItems: 'center', justifyContent: 'center',
      padding: '48px 20px', boxSizing: 'border-box',
      background: '#EDE9E1',
    }}>
      {/* 頁首 */}
      <div style={{ textAlign: 'center', marginBottom: 28 }}>
        <div style={{
          display: 'inline-flex', alignItems: 'center', gap: 8,
          background: '#FAF6F0', border: '1px solid rgba(61,46,38,0.10)',
          borderRadius: 20, padding: '6px 16px',
          fontFamily: '"Noto Sans TC", sans-serif', fontSize: 11,
          color: '#A89484', letterSpacing: 2, marginBottom: 12,
        }}>
          <span style={{ width: 6, height: 6, borderRadius: 3, background: '#B76E79', display: 'inline-block' }} />
          互動 Prototype
        </div>
        <div style={{
          fontFamily: '"Noto Serif TC", serif', fontSize: 22, color: '#3D2E26',
          fontWeight: 500, letterSpacing: 1,
        }}>
          風格 A · 溫柔典雅
        </div>
        <div style={{
          fontFamily: '"Cormorant Garamond", serif', fontStyle: 'italic',
          fontSize: 14, color: '#A89484', marginTop: 4, letterSpacing: 2,
        }}>
          米白 · 奶油 · 玫瑰金
        </div>
      </div>

      <InteractivePhone />

      {/* 切換風格按鈕 */}
      <div
        onClick={() => { window.location.href = 'Wedding Album Style B.html'; }}
        style={{
          marginTop: 16, width: 360,
          display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 10,
          padding: '14px 0', borderRadius: 14,
          background: '#1A1A1A', color: '#FAF6F0',
          cursor: 'pointer', boxShadow: '0 4px 18px rgba(0,0,0,0.18)',
          fontFamily: '"Noto Sans TC", sans-serif', fontSize: 12, letterSpacing: 2,
          userSelect: 'none',
        }}>
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
          <path d="M8 3H5a2 2 0 00-2 2v3m18 0V5a2 2 0 00-2-2h-3M3 16v3a2 2 0 002 2h3m10 0h3a2 2 0 002-2v-3"/>
        </svg>
        切換到風格 B · 現代精緻
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
      </div>

      {/* 說明文字 */}
      <div style={{
        marginTop: 24, textAlign: 'center',
        fontFamily: '"Noto Sans TC", sans-serif', fontSize: 11,
        color: '#A89484', letterSpacing: 1, lineHeight: 1.8,
      }}>
        按 ← → 切換畫面 · 點 ☰ 開啟選單 · 點擊畫面內按鈕互動
      </div>
    </div>
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(<App />);
