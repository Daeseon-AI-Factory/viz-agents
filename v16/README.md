# VIZ V16 — Collaboration

V4 base + 같은 HUD 다중 사용자 공유.

## V4 → V16 변경

- 현재 server.py 는 이미 multi-client WebSocket 지원 → **같은 머신/네트워크 내 여러 탭 sync 됨**
- 진짜 외부 사용자 공유는 ngrok 같은 터널 필요 (별도)
- 향후: 사용자별 커서/하이라이트, 채팅 컴포넌트

## 한계 (V16 의도 대비 현재 구현)

- **현재는 같은 머신 다중 탭만 sync** — 본격 협업 (WebRTC, 사용자별 권한) 미구현
- 보안/인증 없음
- 자세한 명세: `../viz-v16.md`

## 실행
```bash
./start.sh
```
다른 머신에서 접속하려면 ngrok 또는 LAN IP 사용.
