# dev-page — 에이전트 참조

## i18n 필수 (index.html)

`dev-page/index.html`은 **ko / en / es 3개 언어**를 지원하는 단일 파일 i18n 구조입니다. 광고 캠페인 랜딩 페이지로 사용되므로 언어 간 정합성이 중요합니다.

### 동작 방식

- 단일 HTML 파일, `<script>` 내부 `I18N` 딕셔너리에 3개 언어 저장
- 감지 우선순위: URL `?lang=xx` → `localStorage('clpak_lang')` → `navigator.language` → `ko`
- 번역 대상 요소는 `data-i18n="path.to.key"` 또는 `data-i18n-html="..."` (innerHTML용, `<br>` 등 허용)
- 우상단 언어 전환 버튼(`.lang-btn`) — 클릭 시 localStorage에 저장
- 광고 링크 예: `https://claypark.github.io/dev-page/?lang=es`

### 수정 시 반드시 체크

**어떤 문자열이든 추가/변경할 때:**
1. HTML 요소에 `data-i18n` 속성 부여 (경로: 점 표기법 — 예: `apps.jukforest.tagline`)
2. `I18N.ko`, `I18N.en`, `I18N.es` **세 언어 모두** 해당 키 추가/수정
3. 세 언어 중 하나라도 누락되면 해당 언어에서 한국어 기본값이 그대로 노출됨

**앱을 새로 추가할 때:**
- 타일에 `data-i18n="apps.<id>.name"`, `apps.<id>.tagline`, `badge_live`/`badge_dev` 달기
- 디테일 패널에 `apps.<id>.detail_tagline`, `apps.<id>.detail_desc`, 필요 시 `apps.<id>.detail_name`
- `privacy`, `terms` 링크 텍스트에 `data-i18n="privacy"`, `data-i18n="terms"` (공통 키 재사용)

**번역 품질:**
- 직역 금지 — 앱 스토어 short description 톤의 마케팅 카피로
- 영어/스페인어 번역은 Content Creator 에이전트(혹은 번역 전문 에이전트)에 위임 권장
- 스페인어는 반드시 한글 입력기의 ASCII 대체가 아닌 정식 악센트/`ñ`/`¿¡` 사용

**브랜드명 표기:**
- 한글 브랜드 앱은 로마자로: 오운완 → Ounwan, 나루 → Naru, 입소문 → Ipsomun, 더슬러 → Dustler, 소각 → Sogak
- 예외: 대나무숲은 의미 전달 위해 번역 (Bamboo Forest / Bosque de Bambú)
- AMEN, Bagshot은 원래 로마자 — 그대로

### 파일

- `/dev-page/index.html` — 메인 랜딩, I18N 딕셔너리 포함
- 서브 경로(`dev-page/ipsomun/`, `dev-page/dustler/` 등)의 privacy/terms는 아직 i18n 미적용 — 필요 시 별도 작업
