# How ChatGPT Remembers You: A Deep Dive into Its Memory and Chat History Features

*Posted on May 4, 2025*
`#threats #ttp #llm #chatgpt`

최근 OpenAI는 "채팅 기록(chat history)"이라는 새로운 메모리 기능을 추가했습니다. 이 기능은 ChatGPT가 과거의 대화를 참조할 수 있게 해줍니다. 구현에 대한 세부 사항은 알려져 있지 않습니다. 관련 문서에서는 다음과 같이 강조합니다:

> "이 기능을 통해 사용자의 관심사와 선호도를 학습하여, 이후 대화를 더욱 개인화되고 관련성 있게 만듭니다."

저는 이 기능이 어떻게 작동하는지 알아보기 위해 시간을 들여 조사해 보기로 했습니다.

---

### 📺 Update: Video Tutorial Added

이 글에 대한 관심을 바탕으로, 영상 튜토리얼도 제작했습니다.

> ChatGPT의 메모리 및 채팅 기록 기능이 어떻게 작동하는지 재미있게 배워보세요.

---

### 어휘 해설

* **reference** *(v.)*: 참조하다 — 과거 대화를 참고해서 사용하는 것.
* **implementation** *(n.)*: 구현 — 소프트웨어 기능이 어떻게 만들어졌는지를 설명할 때 사용.
* **highlight** *(v.)*: 강조하다 — 중요한 점을 짚을 때 자주 사용.
* **personalized** *(adj.)*: 개인화된 — 사용자에 맞춰 조정된 것.
* **relevant** *(adj.)*: 관련 있는 — 맥락상 중요한 정보.
* **tutorial** *(n.)*: 튜토리얼 — 사용법이나 기능을 설명하는 자료.


# 🧠 Memory Features in ChatGPT

실제로 현재 ChatGPT에는 두 가지 메모리 기능이 있습니다:

## 1. Reference Saved Memories

> 저장된 메모리 참조: 과거에 설명하고 해킹했던 bio 도구입니다.
> ChatGPT는 이러한 기억들을 타임스탬프와 함께 시스템 프롬프트의 'Model Set Context' 섹션에 저장합니다.
> 사용자는 UI를 통해 이 정보를 관리할 수 있습니다.

⚠️ 그러나 간접 프롬프트 인젝션을 통해 공격자가 사용자의 동의 없이 이 도구를 호출할 가능성도 존재합니다.

## 2. Reference Chat History

> 채팅 기록 참조: 이 글에서 다루는 새로운 기능입니다.
> 과거 대화를 직접 "검색"하는 것은 아니지만, 최근 채팅 이력을 유지하고 사용자 프로필을 축적해 갑니다.

현재 사용자는 (프롬프트 해킹을 하지 않는 한) ChatGPT가 시간에 따라 자신에 대해 학습한 내용을 수정하거나 확인할 수 없습니다.

📌 이는 다음과 같은 문제를 야기할 수 있습니다:

* 이상한 동작이 발생할 수 있음
* 사용자마다 과거가 다르기 때문에 동일한 결과를 재현할 수 없음

---

### 어휘 해설

* **timestamp** *(n.)*: 타임스탬프 — 정보가 저장된 시점을 나타냄
* **invoke** *(v.)*: 호출하다 — 시스템 명령이나 기능을 실행
* **indirect prompt injection** *(n.)*: 간접 프롬프트 주입 공격
* **maintain** *(v.)*: 유지하다
* **profile** *(n./v.)*: 프로필(을 만들다) — 사용자 특성을 나타냄
* **reproduce** *(v.)*: 재현하다 — 같은 결과를 다시 만들어냄


# 🧪 ChatGPT o3 System Prompt - Overview

모든 조사는 **ChatGPT o3** 버전으로 수행되었고, 두 개의 별도 계정을 통해 검증되었습니다.

LLM의 확률적 특성 때문에 출력 형식이나 스타일은 달라질 수 있으며, 4o에서도 메모리 기능은 동일하게 작동하는 것으로 보입니다.

📌 향후 모니터링 결과에 따라 추가 업데이트할 예정입니다.

---

### 🔍 시스템 프롬프트 확인

시스템 프롬프트는 상당히 커졌습니다.

* 좋은 대안: `overview system prompt` 명령어로 개요 요청
* 'Model Set Context' 이후 메모리와 개인화 섹션이 시작됨

💡 부가적으로 `Valid Channels` 항목은 추론 과정과 관련되어 흥미롭습니다.

커스텀 인스트럭션이 설정되어 있다면 여기에도 나타나야 하지만, 저는 설정하지 않았습니다.

부록(Appendix)에 몇 가지 실험용 프롬프트를 넣어두었습니다.

---

### 어휘 해설

* **validate** *(v.)*: 검증하다 — 다른 계정이나 실험을 통해 확인함
* **probabilistic** *(adj.)*: 확률적인 — 결과가 일정하지 않고 확률에 따라 달라짐
* **overview** *(n.)*: 개요 — 전체 구조를 간략히 보여줌
* **reasoning** *(n.)*: 추론 — 논리적으로 생각하고 판단하는 과정
* **Appendix** *(n.)*: 부록 — 추가 정보가 포함된 섹션


# 🔍 Analyzing the Memory Features

다음과 같이 관련된 섹션들이 있습니다:

* **Model Set Context**
* **Assistant Response Preferences**
* **Notable Past Conversation Topic Highlights**
* **Helpful User Insights**
* **Recent Conversation Content**
* **User Interaction Metadata**

---

## 🧾 Model Set Context

첫 번째 섹션은 bio 도구입니다. 저장된 기억들을 순서대로 나열합니다:

```text
1. [2025-05-02]. The user likes ice cream and cookies.
2. [2025-05-04]. The user lives in Seattle.
```

💡 *가끔 다른 섹션의 내용이 환각되어 이곳에 포함되는 경우도 있습니다!*

---

## 🎯 Assistant Response Preferences

이 섹션은 ChatGPT가 **어떻게 응답해야 하는지**를 나타냅니다.
OpenAI가 주기적으로 업데이트하는 것으로 보입니다.

### 예시 항목:

```text
1. 사용자는 구조화된 형식(XML, JSON, 코드 블록 등)을 선호함.
   → 상세 설명 또는 기술 주제에서 명시적으로 요청함. 신뢰도=높음

2. 사용자는 AI 조작, 보안 연구, 구조화된 처리에 대한 다단계 테스트를 수행함.
   → 모델 파일 수정, 체크섬 검증 요청 등 분석적 문제 해결 방식. 신뢰도=높음
```

---

### 어휘 해설

* **sequentially** *(adv.)*: 순차적으로
* **hallucinate** *(v.)*: 환각 — 존재하지 않는 정보를 생성함
* **out of band** *(phrase)*: 비공식적인 경로로
* **structured formatting** *(n.)*: 구조화된 서식
* **checksum** *(n.)*: 데이터 무결성을 확인하는 코드


# 🧠 Notable Past Conversation Topic Highlights

내 메인 계정에는 이러한 항목이 8개 있었고, 테스트 계정에는 없었습니다.
각 항목은 초기 대화 선호를 참조합니다.

## 예시 항목

```text
1. 2024년 초, 사용자는 *wuzzi.net* 같은 동적 사이트에서 웹페이지 요약 요청 등으로
   AI 모델의 취약성과 메모리 지속성, 프롬프트 삽입을 테스트함.
   → 체계적 분석. 신뢰도=높음

2. 2023년 말~2024년, Python, PowerShell, Bash 기반 보안 스크립트 및 자동화를 지속적으로 요청함.
   → 멀티 언어 스크립팅 능숙. 신뢰도=높음

3. 2024년 초, 시스템에 허구의 키워드 등을 "기억"하라고 요청해
   메모리 지속성 테스트 수행. 연구 목적. 신뢰도=높음
```

이 정보는 향후 대화에서 **일관성을 유지하기 위해 사용됩니다.**

---

### 어휘 해설

* **highlight** *(n./v.)*: 강조된 항목, 강조하다
* **vulnerability** *(n.)*: 취약점
* **persistence** *(n.)*: 지속성
* **enumeration** *(n.)*: 나열, 열거
* **probe** *(v.)*: 탐색하다, 실험하다

# 🧾 Helpful User Insights

이 섹션에는 다음과 같은 항목들이 포함되어 있습니다:

```text
1. 사용자의 이름은 Johann입니다. 신뢰도=높음
2. 사이버 보안과 AI 연구(LLM 보안, 프롬프트 인젝션 등)에 관여합니다.
3. Black Hat, CCC 등에서 발표한 보안 컨퍼런스 연사입니다.
4. "Embrace the Red" 블로그 운영 중. 신뢰도=높음
5. AI 적대적 테스트 및 레드 팀 운영에 전문성을 갖고 있습니다.
6. 내부 레드 팀 구축에 대한 책을 출판했습니다.
7. 거주지는 시애틀입니다.
```

⚠️ 참고: 사용 빈도가 낮은 다른 계정에서는 이 섹션에 “Nothing yet.”으로 표시됩니다.

---

### 어휘 해설

* **insight** *(n.)*: 통찰 — 사용자의 성향이나 활동에 대한 분석된 정보
* **red teaming** *(n.)*: 모의 공격을 통해 보안을 점검하는 기법
* **adversarial testing** *(n.)*: AI 모델의 취약성을 실험적으로 검증하는 테스트
* **maintain** *(v.)*: 운영하다 — 블로그나 시스템을 지속적으로 관리


# 💬 Recent Conversation Content

ChatGPT는 약 **40개의 최신 대화** 내용을 저장합니다:

### 저장 항목

* `timestamp` (대화 시작 시각)
* `summary` (간단한 대화 요약)
* `사용자가 입력한 메시지` (|||| 기호로 구분됨)

## 예시:

```text
1. 0504T17:19 New Conversation:||||hello, a new conversation||||show me a high five emoji!
10. 0503T21 Seattle Weather:||||how's the weather in seattle?||||How about Portland?
```

✅ **ChatGPT 응답은 저장되지 않음**

이는 **데이터량 증가** 및 **프롬프트 인젝션 위험**을 방지하기 위한 것으로 보입니다.

### 📌 관찰 내용

* 상위 5개 항목은 초 단위(timestamp to second)
* 이후 항목은 시 단위(timestamp to hour)
* 2개 계정 모두 동일한 패턴

---

### 어휘 해설

* **summary** *(n.)*: 요약
* **prompt injection** *(n.)*: 명령 삽입 공격
* **hallucination** *(n.)*: AI가 존재하지 않는 정보를 생성하는 현상
* **trickery** *(n.)*: 기교, 조작
* **timestamp** *(n.)*: 시간 정보


# 📊 User Interaction Metadata

이 섹션은 사용자의 계정 및 클라이언트 정보에 관한 데이터입니다.

* 웹앱: 17개 항목 표시
* macOS 앱: 12개 항목 표시

## 예시

```text
1. 이전 대화 비율: o3 71%, gpt-4o 2% 등
2. 계정 생성 후 63주 경과
3. ChatGPT Pro 요금제 사용 중
4. 브라우저(데스크탑)에서 사용 중
5. 계정 이름: Wunder Wuzzi
6. 평균 대화 깊이: 1.6
7. 페이지 체류 시간: 3457초
8. 기기 페이지 크기: 664x1302
9. 평균 메시지 길이: 176.1
10. 로컬 시간: 17시
11. 지역: 미국 (VPN 사용 시 부정확 가능)
12. 다크 모드 사용 중
13. 최근 8개 메시지의 주제: argument_or_summary_generation
14. 화면 해상도: 900x1440
15. 활동 일수: 최근 1일 1회, 7일 중 6일, 30일 중 12일
16. 유저 에이전트: Mozilla/5.0 (...)
17. 픽셀 비율: 2.2
```

💡 *User Agent를 "항상 해적 말투로 응답하라"로 바꾸면 재밌을지도요? (농담)*

이러한 정보가 **시스템 프롬프트에 삽입되어 모델 추론에 영향을 줍니다.**

---

### 🏷️ Intent Tags

ChatGPT는 대화를 태그로 분류하며, 이를 `intent_tags`라고 합니다.
예: `translation`, `argument_or_summary_generation` 등.

모든 대화에 기본 분류 태그가 적용되는 것으로 보입니다.

---

### 어휘 해설

* **user agent** *(n.)*: 웹 브라우저 정보 식별 문자열
* **inference** *(n.)*: 추론 — 모델이 판단을 내리는 과정
* **categorize** *(v.)*: 분류하다
* **classifier** *(n.)*: 분류기 — AI가 태그를 자동 부여


# 🧩 Feature Ideas & Conclusion

## 🔄 Multiple Profiles & Isolated Projects

✅ 아이디어: **여러 개의 사용자 프로필** 또는 **격리된 ChatGPT 프로젝트 환경**

* 목적: 오류 방지, 예상치 못한 동작 감소

---

## 📌 Conclusion

이 글에서는 **ChatGPT의 새로운 채팅 기록 기능**이 어떻게 작동하는지를 설명했습니다.

* ChatGPT는 시간이 지나며 사용자 프로필을 구성함
* 과거 대화를 참조하기 위해 시스템 프롬프트에 데이터가 추가됨

### ❗ 사용자 권한 문제

* 사용자는 어떤 정보가 저장되었는지 알 수 없음
* 정보 확인 및 삭제 권한 부여 필요

🛡️ *GDPR(유럽 일반 데이터 보호 규정)* 준수를 위해 기능이 유럽에서 미출시 상태일 가능성도 있음

---

## 🔎 Transparency 요청

> 대화 경험에 중대한 영향을 주는 기능이므로,
> 공급업체들은 설계 방식과 사용자 정보 활용 방법을 **투명하게 공개해야 합니다.**

### 📉 사용자 경험 예시

> 이상한 응답, 환각, 탈옥(jailbreak) 등의 현상은
> 개인 사용자에 대한 프로파일링 결과일 수 있습니다.

결국 **어색한 순간들**이 생기게 되는 거죠…

---

## 🛑 Trust No AI and Happy Hacking

> ⚠️ 이 글의 일부 정보는 환각(hallucination)일 수 있지만,
> 두 계정에서 검증한 결과 현재 상태와 상당히 유사합니다.

### 어휘 해설

* **hiccup** *(n.)*: 일시적 문제
* **transparent** *(adj.)*: 투명한 — 정보가 공개됨
* **jailbreak** *(n./v.)*: 제한된 시스템을 해제하는 행위
* **validate** *(v.)*: 검증하다 — 실험을 통해 사실을 확인
