# Multi_DeployGo
## 카카오클라우드스쿨 최종프로젝트
## ☁️ 프로젝트 소개영상
https://www.youtube.com/watch?v=89994MummJo&list=LL&index=9&ab_channel=cloudkakao

### 구조도
![image](https://user-images.githubusercontent.com/44285158/208251820-5f6b22a6-ae53-4693-a6bc-1407a81d5b33.png)

[Bluegreen update]
![image](https://user-images.githubusercontent.com/44285158/208251849-243b0a8a-36ec-42a3-898e-f83cd856ce4f.png)

[Canary update]
![image](https://user-images.githubusercontent.com/44285158/208251866-6167f9c4-82bf-4425-999a-5e6ce02e654b.png)

<br />

## ☁ 웹서비스 소개
### 1️ 로그인 페이지
![image](https://user-images.githubusercontent.com/44285158/214204036-16105784-c0bf-448e-90b6-23ded9cde2d7.png)

### 2️ 클러스터등록 페이지
![image](https://user-images.githubusercontent.com/44285158/214203963-91552181-e136-4191-8940-33d0e0b4ba3a.png)

### 3️ 앱 등록 페이지
![image](https://user-images.githubusercontent.com/44285158/214203989-954a023c-74d1-4f24-beca-d94ee1e02b28.png)

### 4️ 배포 페이지
![image](https://user-images.githubusercontent.com/44285158/214204267-e17261f3-f508-47ab-bb40-5b21e53cddae.png)

[롤링업데이트]
![image](https://user-images.githubusercontent.com/44285158/214204706-e07d98b5-eaef-41b4-8a7e-3dc532a3298e.png)

[블루그린]
![image](https://user-images.githubusercontent.com/44285158/214204722-5fffb071-c9bc-48fb-80e5-7118cfd06f49.png)
![image](https://user-images.githubusercontent.com/44285158/214204734-0f312b4e-57a5-496b-b7fb-958d433b2313.png)

[카나리]
![image](https://user-images.githubusercontent.com/44285158/214204746-8cd9d486-2657-4cec-aa98-c328c8d6d28b.png)
![image](https://user-images.githubusercontent.com/44285158/214204756-321db01d-a9b9-486e-9c9a-872db675d699.png)


### 5 관리자 승인 페이지
![image](https://user-images.githubusercontent.com/44285158/214204803-959dabd5-4820-4355-a410-f5966ca93df7.png)

### 6 배포이력 페이지
![image](https://user-images.githubusercontent.com/44285158/214204333-1f107cd0-b711-46b2-b88a-6cf0fdc36bdf.png)


<br />

## ☁ 실행방법

- python -m venv venv
- pip install -r requirements.txt
- python manage.py makemigrations
- python manage.py migrate
- python manage.py runserver

## ☁ 기술 스택

- Python 3.9
- Django 4.1.3
- Bootstrap4
- Kubernetes 1.22
- ArgoCD 2.5.2
- MariaDB 10.6

 
<br />
