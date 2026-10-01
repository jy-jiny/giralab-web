## 2026-10-01 · 프로젝트 화면과 Ready 문구 1.5.54

소스 `5543cdf`의 전체 Vite 빌드를 게시한다. 선택과 상세 문구를 프로젝트로 통일하고, 프로필에는 실제 티어를 표시한다. 프로젝트 상세는 작은 화면에서도 세로 스크롤 없이 표시되며 Ready는 신선한 재료를 준비한다는 문구를 쓴다. 파일별 해시와 소스는 `site/source-build.json`에 기록한다. 기존 게임·인증 API와 기록을 유지하며 서버·DB 변경은 없다. 실제 휴대폰 확인은 별도다.

## 2026-09-30 · 정지 메뉴와 메인 이동 종료1.5.52

정지 화면의 계속하기 아래에서 새로 시작하며 하트1개 확인을 거친다. 명시적 메인 이동은 이번 판을 종료하고 이어하기를 남기지 않는다. 최신 전체/티어별 순위 기능도 포함한다. 소스4d9df3e1de0f23e67facfc1381bc402e1f85992c의 전체 Vite 웹 빌드, 재시작/메인 종료14상황133·하트20·언어45·순위84·계정28 검증. 실제 게시 검증은 배포 워크플로와 원본 저장소 배포 근거에 기록한다. 실계정 Google 로그인·실기기는 별도이며 이 작업의 서버/DB 변경은 없다.

# GiraLab Web

## 2026-09-30 · 전체·티어별 순위1.5.51

기존 TOP 5 아래 전체·6티어별 순위 보기를 추가한다. 인증된20명 페이지와 항상 표시하는 내 순위, 기존 다크·골드 및 티어 배지를 제공한다. 앞서 배포된 새로 시작 기능과 기존 계정·기록·API 주소를 유지한다.

소스PR122의56fc77f 전체 Vite 빌드이며 후속 변경은 검사/개발 기록이다. 실제 웹 번들에서 순위84·재시작73·신고55·계정28·하트 검사를 통과했다. 파일38개의 정확한 해시는 source-build.json에 기록한다. DB20260930091545와 게임 함수29/17 적용, 소스 main fa80858 및 웹 PR26/main 배포 완료. 실제 URL의38파일과 격리 순위84검사 통과. 실제 Google 로그인·휴대폰 확인은 별도다. iOS는 Actions 예산으로 미실행이며 전체 소스 CI 성공으로 기록하지 않는다.

## 2026-09-30 · 중간 새로 시작1.5.50

게임 상단에서 새로 시작을 누르고 하트1개 사용을 확인하면 기존 판을 정상 종료한 뒤 새 판을 시작한다. 취소는 원래 진행/일시정지를 유지하며 최고 기록·도감과 기존 API/설정을 보존한다.

소스5a46037 전체 Vite 빌드의 새 재시작8상황73·하트20·계정28·신고55·언어45검사를 격리 API로 통과했다. 영어 결과 대기 단발 실패는 동일 빌드 재검증 통과이나 원인은 미확인이다. 모달 종료를 기다리는 시험 코드 보완은9f011d5로 구분한다. 정확한 파일 해시와 출처는 site/source-build.json에 기록한다. 서버/DB 변경·실제 Google 로그인/휴대폰 검증은 없다. 기존 웹 펫 API404 후속 배포는 별도다.


## 2026-09-30 · 입체 발바닥·큰 장착 펫1.5.47 공개 웹

미장착에는 테두리 없는 입체 발바닥과 한 줄 “눌러서 펫 설정”을 표시한다. 장착하면 실제 그림 높이가 발바닥의 최소1.74배인 펫과 아래 레벨을 보여준다.11종 원본·중앙 배치·작은 화면·계정/기록/설정은 유지한다.

소스PR118의 전체 Vite 빌드에서 펫601·계정28·신고54·하트 검사를 통과했다. 정확한 빌드 소스·CI·파일 해시는 source-build.json에 기록하며 게시 후 확인은 별도로 수행한다. 서버/DB 변경 없음. 기존 웹 펫 인증 프록시404(ISS-20260930-001)와 실제 Google 로그인·휴대폰 확인은 이번 격리 UI 검사로 해결 또는 검증됐다고 판단하지 않는다.

## 2026-09-30 · 골드 펫 타일1.5.46 공개 웹

프로필의 미장착 펫 칸을 은은한 골드 면과 실선 테두리로 바꾸고 발바닥 아이콘과 ‘눌러서 / 펫 설정’ 안내를 표시한다. 닉네임 뒤 남는 영역의 중앙 배치와 장착된 펫 그림·레벨을 유지한다. 소스PR114의 전체 Vite 빌드이며 기존 공개 API·계정·기록·하트·설정·신고 기능을 보존한다.

전체 빌드의 펫497·신고54·계정28 및 하트 검사를 수행하고, 게시 후 전체 파일 해시와 실제 URL의 격리 펫 화면을 확인한다. 소스·CI·해시 근거는 source-build.json에 기록한다. 이번 서버/DB 변경은 없으며, 기존 웹 펫 인증 프록시404(ISS-20260930-001)는 별도 서버 수정 사항이다. 격리 API 화면 검사를 실제 계정의 펫 기능·Google 로그인·실기기 검증으로 계산하지 않는다.

## 2026-09-30 · 문제 신고 상세 설명1.5.45 공개 웹

문제 종류 선택 아래에 선택 입력인 상세 설명을 제공한다. 여러 줄·최대1,000자이며, 빈 설명도 기존처럼 접수한다. 전송 실패와 같은 ID 재시도에서는 작성한 내용을 유지하고 접수 후 비운다. 한국어/영어와 좁거나 낮은 화면을 지원한다.

소스PR109의 전체 Vite 빌드이며 기존 투명 펫11장·가운데 정렬된 펫 칸·공개 API 경로·계정/기록을 보존한다. DB20260929232312와 인증 서버를 먼저 적용하고 실제 합성 신고의 설명 저장·중복 방지·초과 입력 거절을 검증한 뒤 시험 신고2건을 정리했다. 로컬 실제 웹 자산에서 신고54·계정28·하트 검사를 통과했고, 게시 후 모든37파일의 해시를 확인한다. 소스/CI/게시 근거는 source-build.json에 남긴다. 실제 휴대폰 키보드·Google 로그인 확인과 iOS 전용 예산 제한은 별도다.

## 2026-09-30 · 투명 펫 그림1.5.44 공개 웹

펫 도감과 장착 칸에 투명 PNG11장을 표시하고 검은 배경을 제거한다. 프로필의 펫 칸은 닉네임 뒤 남는 공간의 가운데에 두고 미장착일 때 “눌러서 / 펫 설정”(영어 지원)을 표시한다. 기존 펫 능력·성장·계정/점수/도감·공개 API 경로를 유지하며 서버/DB 변경은 없다.

소스PR107과 동일 제품 트리의 전체 Vite 빌드를 검증해 게시한다. source-build.json에 전체 파일 해시·원본 main 병합·CI 상태를 기록하며 iOS 전용 CI는 Actions 예산으로 실행되지 않은 한계를 구분한다. 실제 휴대폰 설치와 Google 로그인을 검증한 것으로 표시하지 않는다.

## 2026-09-29 · 펫 기능1.5.43 공개 웹

펫11종 능력·Lv.1~10 성장·장착/해제·도감을 적용한다. 프로필 오른쪽 미장착 칸은 빈 점선 네모이며 그림은 후속이다. 기능 확인용으로 첫 조회에11종 Lv.1 지급, 기본 장착 없음. 기존 공개 API와 계정/점수/도감·구형 판을 보존한다.

DB20260929102158과 서버28/16/14를 먼저 적용했다. 동일 소스의 전체 웹 빌드에서 펫81·게임139·하트20·언어45·계정28상황을 격리 검증했다. 소스PR105·maindb55509와 Android/인증/공통/문서 CI·동일 소스 서버 재검사 성공을 확인했다. iOS 전용은 예산 제한으로 미실행이다. 실제 게시 파일은 Pages 검증 후 대조하며 source-build.json에 소스·CI와 전체 파일 해시를 기록한다. 운영 시험 점수는 만들지 않는다. 실제 휴대폰과 장기 밸런스는 후속이다.

## 2026-09-29 · 투명 기린 티어1.5.42 공개 웹

프로필과 티어 기준표에 학부생·학사·석사·박사·교수·명예교수의 기린 배지6장을 표시한다. 외곽은 실제 알파 채널이 있는 투명 PNG이며 원본 선택 그림의 배경색 사각형을 제거했다. 좁은 화면과 조회 전후 레이아웃을 유지하며 등급 계산·계정/기록·기존 공개 API는 변경하지 않는다.

원본 소스8698000 기반 전체 Vite 웹 빌드이며 최종 소스·빌드 해시·검증 CI는 `site/source-build.json`에 기록한다. 로컬 화면 검사와 Pages 게시 후 파일/화면 검사를 구분한다. 운영 시험 기록은 만들지 않으며 실제 휴대폰 확인은 별도다.

## 2026-09-29 · 옵션·계정1.5.41 공개 웹

옵션을 게임 설정/게임 설명/도감/계정 관리/문제 신고 순서로 정리하고 사운드·언어는 하위 설정에 묶었다. 계정의 확인된 표시 정보를 재사용하며 로그인 중 중복 복구를 숨기고 삭제 행과 신고 버튼을 정렬했다. 기존 공개 API·계정/기록·게임 규칙과 하트를 유지한다. 원본 소스2b7aced 기반 전체 웹 빌드·20자산·격리 계정28상황/게임139/하트20/신고36/언어45 및 독립 배포 전 검사를 통과했다. 원본 main 반영 및 Android 관련 CI를 확인했다. iOS 전용 CI는 예산 제한으로 미실행이며 실제 폰 확인은 별도다. 이 변경은 Pages CI 검증 후 게시한다. 실제 소스와 상태는 site/source-build.json을 따른다.

## 2026-09-29 · 조합·게이지·종료 즉시 반영과 비동기 검증

Android 1.5.39와 같은 소스의 전체 Vite 웹 빌드다. 새 판은 기기의 같은 입력 시계로 조합·게이지 감소·종료를 즉시 표시하고, 게임 중 입력을 계속 보내 서버가 재료 버퍼와 공유 규칙으로 검증한다. 이전 입력과 종료를 확정한 뒤 다음 판을 Ready/Go에서 시작하며 분석·랭킹 조회를 기다리지 않는다. 기존 공개 API 주소·계정·기록과 구형 진행 판 계약을 유지한다.

DB와 호환 서버를 먼저 배포한다. 실제 웹 빌드에서 입력 시각·즉시 게이지/종료·다음 판·연결 대기·기록·하트를 격리 검증하고, 게시 후 전체 20파일의 해시와 화면을 대조한다. 60초 넘게 전달되지 못한 입력은 시간 검증에 실패할 수 있다. 운영 시험 점수/신고는 만들지 않으며 실기기 체감은 별도 확인한다. 정확한 소스와 CI는 `site/source-build.json`에 기록한다.

## 2026-09-29 · 버퍼 플레이·연결 대기30초 보호

Android1.5.38과 같은 공통 소스의 전체 Vite 웹 빌드다. 잠깐의 통신 실패는 받은 재료로 계속 진행하고 실제로 진행이 막힐 때만 원인별 로딩 대기를 표시한다. 폭탄·콤보·슬로우 시계를 최대30초 보호하며 시간 초과는 메인 복귀/복구 후 종료 확인으로 처리한다. 수동 일시정지·앱 이탈·계정/기록과 기존 신고/시각 표시·결과 화면·로비 안정화를 유지한다.

실제 웹 빌드의 대기·결과·게임·하트·계정 화면과20개 자산 해시를 격리 검증한다. 게시 후 실제 URL도 동일하게 검사하며 운영 시험 점수/신고를 만들지 않는다. 정확한 소스와 CI는 site/source-build.json을 따르고 실기기 체감은 별도다.

## 2026-09-29 · 신고 시각·종료 버튼 수정 (1.5.37)

Android1.5.37과 같은 공통 소스의 전체 웹 빌드다. 문제 신고 목록에 날짜·시작~최근 기록 시각을 표시하며 결과 확인 대기/완료 창 바깥의 신고 버튼을 제거했다. 메인→옵션/일시정지 신고와 접수 성공1.5초 후 자동 닫기를 유지한다. 격리 신고34·게임139·결과70·하트20·계정23 검사를 실행했다. 기존 공개 API·로그인·그림·음악을 보존하고 운영 시험 기록은 저장하지 않았다. 실제 사용자 과거 로그 누락 여부와 실제 폰 확인은 별도다. 최종 소스/CI는 source-build.json을 따른다.

## 2026-09-28 · 결과 확인 안내와 완성된 기록 표시

Android 1.5.28과 같은 공통 소스의 전체 Vite 웹 빌드다. 게임 종료 후 작은 “기록 확인 중…” 안내를 보여주고, 서버 확정 점수와 검증된 분석이 준비되면 결과 창을 표시한다. 조회 실패 재시도·메인 이동·구형 분석·연결 복구와 기존 진단/신고를 유지한다. 실제 빌드에서 결과 전환8상황56개·게임139·하트20·계정22개 시나리오를 격리 검증한다. 하트 배포 fixture도 응답 판 ID와 분석 판 ID를 일치시킨다. 정확한 검증/게시 소스는 `site/source-build.json`에 기록하며 실제 폰 체감은 별도다.

## 2026-09-28 · 제한된 로컬 진단과 문제 신고

Android 1.5.27과 같은 공통 소스의 전체 Vite 웹 빌드다. 주요 사건을 기기에 제한 보관하고 변경 시 10초 간격으로 비동기 저장한다. 문제 신고에서 사용자가 선택한 기록만 서버에 보내며 용도와 7일 보관·자동 삭제를 안내한다. 닉네임·이메일·계정 UUID·토큰·자유 입력·원문 오류·화면/음성은 진단 payload에서 제외한다. 동의·정식 고지 판단은 TBD다.

실제 웹 빌드의 신고 20개·게임 139개·시작 176개·하트 20개·계정 22개 시나리오와 20개 파일 해시를 격리 검증했다. 소스맵은 공개 자산에 넣지 않고 비공개로 보관한다. 기존 웹 API 주소·로그인·기록·그림·음악을 유지한다. 서버/DB 접수·중복 방지·시험 자료 삭제를 확인했고 운영 게임 시험 점수는 만들지 않았다. PC ON/OFF 부하 비교는 원본 소스의 근거 문서에 기록하며 실제 휴대폰 측정은 별도다. 정확한 소스와 CI·배포 결과는 `site/source-build.json`을 따른다. 아래 문단은 이전 배포 이력이다.

## 2026-09-28 · 보조 저장 실패의 불필요한 일시정지 수정

Android 1.5.26과 같은 원본 6087c34의 전체 Vite 웹 빌드다. 서버의 정상 게임 응답 뒤 최고점·도감의 기기 보조 저장이 실패해도 통신 오류로 잘못 처리하거나 일시정지하지 않게 한다. 저장 오류/재시도·메모리 진행도, 실제 게임 큐/통신 오류·앱 전환 보호 멈춤, 기존 공개 API/로그인/기록/그림/음악은 유지한다.

전체 멈춤 경로 감사와 격리 클라이언트 515개·24조건 147개, 실제 웹 계정 UI 22개·게임/시작/하트 회귀를 통과했다. 20개 자산 해시와 별도 공개 fixture를 게시 전후 검증한다. 원본 Android·인증·서버 저장·경계·문서 CI는 통과했고 iOS 전용 CI는 예산 제한으로 미실행이다. 서버/DB 변경이나 운영 시험 기록은 없으며 실제 기기 확인·원래 제보와의 인과·새 진단 수집기 구현은 포함하지 않는다. 정확한 소스/CI는 `site/source-build.json`에 기록한다.

## 2026-09-27 · 즉시 낙하 모션 1.5.23 배포

Android 1.5.23과 같은 소스를 전체 Vite 웹 빌드로 게시한다. 재료가 초반에 순간 이동하듯 보이던 곡선을 가속 낙하와 작은 착지 반동으로 바꾸고, 생성 선대기 0ms·전체 180ms·서버 규칙·공개 API 주소·기존 기록을 유지한다.

실제 웹 번들의 낙하 궤적·같은 열 3회·지연 ACK 189개, 성공 연출 68개·게이지 24개·UI 138개·하트 20개와 독립 공개 배포 검사를 통과했다. 게시 전후 20개 파일 해시와 실제 공개 URL의 동일 검사를 확인하며 게임·인증 요청은 격리 fixture로 처리한다. 정확한 원본 커밋과 CI 결과는 `site/source-build.json`에 기록한다. 실제 휴대폰 체감 확인은 별도다.

## 2026-09-27 · 중복 팝업·콤보 시간 수정 배포

원본 main `515a718`의 Android 1.5.22 런타임을 전체 Vite 웹 빌드로 게시한다. 같은 성공의 지연 응답으로 팝업과 콤보 시간이 재시작하지 않게 하고, 게이지 감소 표시는 확인된 성공마다 한 번 표시한다. 기존 공개 API·로그인·기록 저장 영역·승인 그림·음악을 보존한다.

중복 연출 68개·게이지 24개·기존 UI·언어·하트·계정 fixture를 통과했다. 독립 배포 검사는 현재 규칙에 맞춰 완전 새로고침 시 준비 중이던 이전 판도 종료하고, 다음 새 게임과 재시도에만 새 하트를 쓰는지 확인한다. 이전 준비 판 재사용 설명은 당시 동작이다. 게시 전후 20개 자산 해시와 실제 공개 화면을 검사하며 운영 시험 기록은 만들지 않는다. 원본 CI의 iOS 전용 검사는 예산 제한으로 미실행이고 Android·서버·인증·경계·문서 검사는 통과했다.

## 2026-09-27 · 메인 시작 버튼 배포 준비

Android 1.5.17과 같은 소스의 전체 Vite 웹 빌드를 게시한다. 아직 시작하지 않은 준비 판은 게임 시작, 실제 playing/paused 판은 계속하기로 표시하며 버튼을 랭킹 아래 하단에 배치한다. 한국어/English·Ready → Go·기존 서버 재료 버퍼를 함께 포함한다. 기존 게임/인증 주소와 플레이어 기록을 유지한다.

게시 전후 파일 해시와 격리 브라우저의 시작 문구·준비 판 재사용·하단 위치·한 판 더·결과 화면을 검사한다. 운영 시험 계정과 기록을 만들지 않으며 실제 게시 결과는 후속 근거에 기록한다.

## 2026-09-26 · 하트와 결과창 통합 배포

원본 main `a00f0a08482249ea42e993de04f27d005fb17910`의 전체 Vite 빌드를 게시한다. Android 1.5.13과 같은 상단 하트·게임 시작 배치·프로필을 사용하며, 웹의 모든 새 판과 재시도는 서버에서 하트 1개를 차감한다. 무료 연습과 결과 점수 변화 차트를 제거하고 결과 공유·한 판 더·메인으로 버튼을 한 줄로 표시한다. 기존 API 주소·로그인·개인 기록·도감·음량 저장을 유지한다.

새 서버 판 흐름은 원본의 게임 UI·하트·계정·낙하 fixture로 검사한다. 과거 로컬 점수 주입 방식의 공개 배포 검사 대신, 검증된 전체 빌드의 20개 SHA-256·승인 이미지/음악 일치와 독립 공개 브라우저 검사를 게시 전후에 실행한다. 공개 fixture는 인공 응답 데이터만 포함하며 실제 게임·인증 API로 요청을 전달하지 않는다. 원본 전체 CI 집계에는 iOS 예산 제한과 결과 업로드 저장 용량 제한이 남아 있으나 실제 Android/서버 검사는 통과했다. `site/source-build.json`에 원본과 검증 범위를 기록한다.

## 2026-09-26 · 첫 로딩·랭킹 대기 개선

원본 [PR #42](https://github.com/jy-jiny/giralab/pull/42)의 `303bf43f0db87d36f22d184faeba8a76e9140888` 빌드다. 인증된 계정 상태 응답을 재사용하여 웹의 사용자 조회 한 번을 줄이고, 랭킹을 개인 기록 복구·백업과 병렬로 읽는다. 실제 준비 완료 뒤 고정 대기를 없애며 승인된 로딩 그림·음악·Netlify 인증·기존 기록과 주소는 유지한다.

PC에서 원본 179개 파일 일치와 빌드 20개 파일의 해시, 모바일 타입·공통 출시 경계·실제 Chromium 20개 시나리오를 확인했다. 공개 배포 검사는 사라진 사용자 조회 대신 계정 상태 응답을 보류하여 50/70% 진행률과 로딩 중 음악·승인 이미지를 확인한다. 완료 뒤 100% 화면을 고정 노출할 것을 요구하지 않고 실제 로그인/로비 전환을 검사한다. 원본 CI와 게시 전후 검증 완료 후 배포하며, 사용자 환경의 실제 지연 개선율은 별도 측정 대상이다. 설치된 앱에는 업데이트가 필요하다.

## 2026-09-23 · Google 로그인 확인과 이전 인증 폐기 완료

사용자가 공개 웹에서 실제 Google 재로그인과 기존 기록 복구 성공을 확인했다. 11:13 UTC 운영 전환으로 이전 인증 RPC 자격·공유 인증 bridge·DB의 이전 HMAC 키 복사본을 폐기했다. 기존 계정·점수·도감·세션 9개 표의 전후 전체 지문이 일치했다. Netlify의 원본 HMAC 키와 새 독립 자격은 유지한다.

새 호스트의 900초 토큰 발급·갱신·재사용 차단·HttpOnly 쿠키·CSRF 검사를 다시 통과했다. 이전 Supabase 인증 주소는 410 UPDATE_REQUIRED를 반환하고 게임 서버는 정상이다. `source-build.json`의 전환 상태만 갱신하며 원본 빌드 커밋과 20개 파일 해시는 유지한다. 아래 절은 이전 배포 이력이다. Android 실기기 설치 확인과 공유 DB 관리자 침해 위험은 별개다.


## 2026-09-23 · 인증 서버 Netlify 분리

2026-09-23 [배포 35848467623](https://github.com/jy-jiny/giralab-web/actions/runs/35848467623)이 성공했다. 게시 전후 계정·게임·로딩·음악·결과 화면 회귀 검사가 모두 통과했고 실제 공개 metadata의 새 인증 URL을 확인했다. 원본 배포 기록은 `jy-jiny/giralab`의 `docs/game/evidence/2026-09-23-auth-isolation.json`이다. 실제 Google 재로그인과 이전 인증 키 폐기는 여전히 별도 확인 단계다.

검증된 원본 `1ddb385dd405bc7bf10a8331fa12b9796689b7db`의 전체 Vite 아티팩트를 반영한다. Google 확인과 쿠키/토큰 갱신은 `https://giralab-auth.netlify.app`에서 처리한다. 기존 게임 서버 주소·계정·점수·도감·음량·종료 음악은 유지한다. 웹 인증 쿠키의 호스트가 바뀌어 Google 로그인이 한 번 더 필요할 수 있다. 이전 인증 자격 폐기는 실제 Google 재로그인 확인 후 진행하며, 이 단계에서 완전한 비밀키 격리 완료로 표시하지 않는다.

CI 아티팩트 ZIP SHA-256 및 원본 tree 일치, 빌드 20개 파일과 기존 이미지/음악 해시를 확인했다. 계정 UI fixture는 배포 metadata의 정확한 게임·인증 API를 가로채며 운영 계정/점수는 쓰지 않는다. 기존 게시 전후 회귀 검사를 유지한다. 최종 게시 결과와 실계정 로그인은 별도 확인 사항이다.


## 2026-09-23 · 짧은 토큰과 웹 쿠키

검증한 원본 `66ec5f80ac7aec5866fbd588eaf85ed6eee376db`의 전체 Vite 빌드를 적용한다. 기존 Supabase의 `giralab-auth`에서 15분 게임 토큰·자동 갱신·HttpOnly/Secure/Partitioned 쿠키를 제공한다. 30일 미사용 또는 Google 확인 후 90일에 재인증하며 계정과 기록은 유지한다. 기존 365일 토큰은 배포 후 7일 내 한 번만 자동 이행한다. 인증 환경과 비밀키까지 격리하는 작업은 후속이다.

게시 전후 게임·계정 검사를 유지한다. 기존 UI fixture에 단기 세션 전송 어댑터를 추가했으며 실제 쿠키·갱신·만료·동시 요청은 원본의 브라우저/PG17 검사에서 별도로 검증했다. 개인 Google 계정 선택과 실기기 조작은 자동 검사와 구분한다.


운영 게시 작업은 `deploy.yml` 한 곳에서 전체 빌드와 게시 전후 회귀 검사를 실행한다. 이전 대시보드·테마 아트 단독 게시기는 `source-build.json`에 새 인증 주소가 있으면 실행을 건너뛰어 과거 번들로의 되돌림을 방지한다. 현재 게시의 계정·게임 검사 조건은 유지한다.

## 2026-09-23 · 판 종료 음악

원본 `2a4dce7c9ac28356de4b8ecf39a206d714fcdbf6`의 전체 Vite 빌드를 반영합니다. 결과 화면에 8초짜리 오리지널 곡 Experiment Complete가 한 번 재생되며, 기존 음악·음소거·기록·Google 로그인은 유지합니다. 새 판을 완료하면 다시 한 번 재생됩니다.

GitHub Actions 예산 해결 후 원본 APK/웹 빌드 `35802601488`이 성공했습니다. 웹 배포 워크플로는 게시 전후 기존 게임·계정 검사와 실제 결과 화면의 종료 음악/재도전 검사를 실행합니다. `site/source-build.json`에 원본 커밋·아티팩트와 파일 해시를 기록합니다. [최종 배포 35805200578](https://github.com/jy-jiny/giralab-web/actions/runs/35805200578)이 성공했으며 게시 전후 게임·계정·로딩·오디오·결과 검사가 모두 통과했습니다. 실제 공개 URL에서 8초/반복 없음/판당 한 번/재도전 후 재생/기존 게임 음악 중단을 확인했습니다. 실계정 Google 인증과 실기기 청음은 별도입니다.

첫 배포 `35804019836`은 게시 전 결과 음악 검증과 GitHub Pages 게시에 성공했으나, 게시 후 로딩/음량 검사에서 메인 복귀 직후 옵션 창 확인이 실패했습니다. 검사는 닫히는 Radix 대화상자와 오버레이가 제거되고 메인 화면이 표시된 뒤 메인의 옵션 버튼을 누르도록 보완했습니다. 음량/음소거/오디오 미지원에 대한 기존 단언은 유지하며, 실패 시 화면과 대화상자 상태를 남깁니다. 보완 후 동일한 전체 게시 전후 검사를 통과했습니다. 검증 증거는 해당 실행의 `giralab-e5-live-verification` 아티팩트에 보관합니다.


The 2026-09-22 web Google login rollout is documented in [WEB_GOOGLE_LOGIN_20260922.md](WEB_GOOGLE_LOGIN_20260922.md). The original API URL and existing records are preserved; publication and actual Google account verification are separate.

Public deployment target for the built GiraLab web app. Source code remains in the private repository.

The 2026-09-22 Google-first release requires Google proof before a new nickname,
restores an existing account automatically, and preserves server records on logout.
The original `giralab-game` API address remains unchanged so saved installation
credentials, account journals and progress keep their existing namespace.
`site/source-build.json` records the exact source tree, file hashes, provider readiness
and the separate status of actual Google-account verification. This release does not
reset server data or publish an app to a store.

Before and after publication, the account suite checks ten isolated login/account
scenarios. Gameplay regressions use a saved linked-player fixture and private-backup
responses, preserving the existing layout, audio, rules, codex and result checks.
Loading checks exercise Google-first entry before nickname input and retain the
same audio element through verified nickname creation. Every game API and Google
credential in these automated checks is a fixture; no production account or score
is created. The earlier release history below describes previous publications.

The 2026-09-21 results release adds the end-of-game report (tier counts, score chart,
final score and image sharing) from the shared app UI. `site/source-build.json`
identifies the source revision and hashes every file in the full Vite build.
Existing loading art, Kitchen Rush music, rules and player storage remain compatible.

Publication runs the existing gameplay, layout, audio and codex checks, plus
`scripts/verify-run-result.py`, before and after GitHub Pages deployment. Game API
requests in browser checks use isolated fixtures; no production scores are written.
The old regression suites inject `scripts/browser-game-driver.js` in the test
runner only. It is never shipped in `site/`; the new result test uses actual DOM
controls and verifies that the release registers no AI game-control tools.

The first publication succeeded, but the live mythic-effect check exposed a test
observer race: React's previous render can still have a null animation object.
The driver now reads the stable presentation timer ref and validates its hook
anchor. Gameplay assertions remain unchanged; the published build is unchanged.


