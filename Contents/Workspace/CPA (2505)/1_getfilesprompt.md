## 프롬프트

지금 우리가 작성하는 파이썬코드는
https://cpa.fss.or.kr/cpa/bbs/B0000368/list.do?menuNo=1200078

이 게시판에 있는 게시글 목록을 탐색하면서 url 리스트를 받아오는거야.

-----
전체 프로세스 다시 설명할게.

### 1. 게시판 목록을 탐색하며 url 크롤링 (지금 작성하는 파이썬 파일)
https://cpa.fss.or.kr/cpa/bbs/B0000368/list.do?menuNo=1200078
페이지에서 게시글 목록이 있는 구조물 위치
//*[@id="container"]/div[2]

### 2. 파싱한 url 리스트 바탕으로 다운로드 할 url 리스트 추정
2024 2차 
pdf
https://cpa.fss.or.kr/cpa/cmmn/file/fileDown.do?menuNo=&atchFileId=daf1c7c3dab84b3a971b3e7b89122f85&fileSn=1&bbsId=B0000368
https://cpa.fss.or.kr/cpa/cmmn/file/fileDown.do?menuNo=&atchFileId=daf1c7c3dab84b3a971b3e7b89122f85&fileSn=2&bbsId=B0000368

위와 같은 url을 바탕으로 규칙을 추정해보면, 2차시험은 총 5과목으로 pdf와 hwp파일 총 10개의 첨부파일이 등록되어 있음을 알 수 있다. 게시물 제목을 바탕으로 1차 혹은 2차시험 여부를 식별할 수 있다.
https://cpa.fss.or.kr/cpa/cmmn/file/fileDown.do?menuNo=&atchFileId={Process1에서 추출한 게시물 id 정보}&fileSn={파일번호1~10}&bbsId=B0000368

마지막의 bbsId=B0000368는 게시판 정보임을 추정할 수 있다. 

문제 및 답안은 zip파일으로 업로드 되는 경우도 있고, 개별파일이 등록되는 경우도 있다.
hwp파일은 필요없지만 어떤 순서로 등록되었을지 알 수 없으므로
파일번호 1~10을 호출해보고 등록되지 않은 번호에 마킹하는 방식이 좋을것 같다.

### 3. Process 2에서 작성한 file url list를 바탕으로 다운로드 실행

이게 전체 흐름이고, 지금은 1번 파이썬 코드 작성해야함. 