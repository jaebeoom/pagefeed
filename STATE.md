# 현재 상태

기준: 2026-07-22 검토 · 커밋된 제품 상태 `5939adf`(2026-06-28).

## 한 줄 목적

공개 목록 페이지의 링크를 정적 RSS 2.0 feed로 만들어 GitHub Pages에 배포한다.

## 현재 제품 형태

- `feeds.toml`의 URL, include/exclude 정규식, 공개 경로와 item 한도를 strict하게 검증한다.
- Python 표준 라이브러리만으로 공개 HTML을 가져와 링크·제목·단순 날짜를 추출한다.
- source별 `min_items`를 충족한 경우에만 XML을 써서 추출 실패가 기존 feed를 덮어쓰지 않게 한다.
- `PAGEFEED_BASE_URL`이 있으면 Atom self-link를 포함한 RSS 2.0 XML을 생성한다.
- GitHub Actions가 test, 비공개 config materialization, generate, Pages deploy를 수행한다.
- 배포 실패는 선택적으로 Telegram으로 알릴 수 있고 workflow에서 알림 경로를 수동 점검할 수 있다.

## 최근 의미 있는 변경

- 2026-05-31 · `e0f64df`: include 뒤에 적용되는 link exclusion pattern을 추가했다.
- 2026-05-11 · `f8a3f4e`: GitHub Actions에서 Telegram 실패 알림을 수동 시험할 수 있게 했다.
- 2026-05-10 · `2aff02a`: Pages 배포 실패가 Telegram 알림으로 이어지도록 workflow를 고쳤다.
- 2026-04-23 · `04f069d`: config·HTTP·extractor·RSS·generator 경계를 분리하고 문서와 tests를 확장했다.
- 2026-04-21 · `cd3195a`: 목록 페이지의 feed title 추출을 개선했다.

## 결정과 불변식

- runtime dependency는 Python 표준 라이브러리로 제한한다.
- cookie, 로그인 session, paywall·CAPTCHA 우회 없이 공개 페이지만 가져온다.
- `output_path`와 `public_path`는 feed 사이에서 유일해야 한다.
- `public_path`는 `/`로 시작하도록 정규화하고 공개 feed 이름은 불투명하게 유지한다.
- `feeds.toml`은 local 또는 Actions secret로 숨길 수 있지만 배포된 XML과 원문 링크는 공개다.
- extractor 변경은 network 없는 fixture test로 검증하고 `min_items` 안전장치를 약화하지 않는다.

## 알려진 빈틈

- HTML 추출은 정규식 기반 best-effort 방식이라 source layout 변경에 자동 적응하지 않는다.
- 날짜 인식은 단순 `YYYY-MM-DD` 형태 중심이며 본문이나 인증 페이지는 처리하지 않는다.
- GitHub Pages를 쓰는 한 생성된 feed와 포함된 원문 URL은 공개된다.

## 다음 후보

- 없음. 실제 source가 `min_items` 아래로 실패할 때 해당 HTML fixture와 최소 extractor heuristic을 함께 추가한다.
