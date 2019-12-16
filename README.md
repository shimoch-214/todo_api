## todo-api

serverless frameworkを利用した簡易的なtodoアプリ用のapiです。

- 構成
  - AWS APIGateway
    - Lambda Proxy
    - Authorizer
  - AWS DynamoDB
  - AWS Lambda

- 実装
  - serverless framework v1.58
  - python 3.7
    - pynamodb

## Installation

```
$ sls install -u https://github.com/shimoch-214/todo_api
```

## Credentials Set Up

AdministratorAccessポリシーを付与したIAMユーザを用意してください。

```
$ sls config credentials --provider aws --key AccessKeyId --secret SecretAccessKey
```

## Deploy

```
$ sls deploy
```

## Tables(DynamoDB)

### usersTable

- Attributes
  - id(PK HASH): string
  - email(GSI1 HASH): string
  - userToken(GSI2 HASH): string
  - expiry: string
  - name: string
  - phoneNumber: string
  - password: string
  - createdAt: string
  - updatedAt: string
  - lastLogin: string
  - deleteFlag: bool

### tasksTable

- Attributes
  - id(PK HASH): string
  - taskListId(GSI HASH): string
  - name: string
  - description: string
  - done: bool
  - userIds: array
  - createdAt: string
  - updatedAt: string
  - deleteFlag: bool

### taskListsTable

- Attributes
  - id(PK HASH): string
  - name: string
  - description: string
  - createdAt: string
  - updatedAt: string
  - deleteFlag: bool

## Usage

### User_Create

ユーザーの作成。

```
$ curl -X POST https://https://xxxxx.execute-api.ap-northeast-1.amazonaws.com/dev/users --data '{"name": "user1", "email": "example1@foo.com", "phoneNumber": "08011112222", "password": "12345678"}'
```

required attributes
- name
- email
- phoneNumber
- password(8文字以上))

登録完了後のレスポンスヘッダーに"access-token"が含まれています。user/login以外へのリクエストヘッダーには"Authorization={token}"を含めてください。

### User_Login

ユーザーのログイン

```
$ curl -X POST https://https://xxxxx.execute-api.ap-northeast-1.amazonaws.com/dev/users --data '{"email": "example1@foo.com", "password": "12345678"}'
```

ログイン完了後のレスポンスヘッダーに"access-token"が含まれています。user/login以外へのリクエストヘッダーには"Authorization={token}"を含めてください。


### User_Update

ユーザーの更新。
更新対象のattributeはname, email, およびphoneNumberです。

```
curl -H 'Authorization: xxxxx' -X PATCH https://xxxxx.execute-api.ap-northeast-1.amazonaws.com/dev/users/{user_id} --data '{"name": "user2", "email": "example2@foo.com"}'
```

user_idとtokenに紐づくidを照合します。照合できなかった場合、status:403で拒否されます。


### User_Delete

ユーザーの削除。
論理削除で実装しています。"deleteFlag"をfalseからtrueに変更します。また参加しているタスクの"userIds"より自身のidを削除します。

```
curl -H 'Authorization: xxxxx' -X DELETE https://xxxxx.execute-api.ap-northeast-1.amazonaws.com/dev/users/{user_id}
```

user_idとtokenに紐づくidを照合します。照合できなかった場合、status:403で拒否されます。

### User_tasks_tasklists

ユーザーの参加するタスク一覧およびタスクリスト一覧を取得。

```
curl -H 'Authorization: xxxxx' https://xxxxx.execute-api.ap-northeast-1.amazonaws.com/dev/users/{user_id}/tasks_tasklists
```

example output

```
{
  "statusCode": 200,
  "userId": "abcd1234",
  "taskLists": [
    {
      "createdAt": "2019-12-05 11:54:39",
      "description": "This is tasklist1",
      "id": "abcd1234",
      "name": "tasklist1",
      "updatedAt": "2019-12-05 11:58:19",
      "tasks": [
        {
          "taskListId": "abcd1234",
          "updatedAt": "2019-12-05 12:12:33",
          "userIds": [
            "abcd1234",
            "bcde2345",
            "cdef3456"
          ],
          "createdAt": "2019-12-05 12:12:33",
          "description": "This is task1",
          "id": "abcd1234",
          "name": "task1",
          "done": false
        }
      ]
    }
  ]
}
```

### Task_Create

タスクの作成。

```
$ curl -H 'Authorization: xxxxx' -X POST https://https://xxxxx.execute-api.ap-northeast-1.amazonaws.com/dev/tasks --data '{"name": "task1", "description": "this is task1", "taskListId": "1234abcd"}'
```

required attributes
- name
- description
- taskListId
- userIds(option)

### Task_Update

タスクの更新。
更新対象のattributeは"name"および"description"です。

```
curl -H 'Authorization: xxxxx' -X PATCH https://xxxxx.execute-api.ap-northeast-1.amazonaws.com/dev/tasks/{task_id} --data '{"name": "task2", "description": "This is task2"}'
```

### Task_Add

タスクにユーザーを追加。
"userIds"(array)に与えられたuserIdsを追加します。

```
curl -H 'Authorization: xxxxx' -X PATCH https://xxxxx.execute-api.ap-northeast-1.amazonaws.com/dev/tasks/{task_id}/add --data '{"userIds": ["abcd1234","dcba4321"]}'
```

### Task_Remove

タスクからユーザーを削除。
"userIds"(array)から与えられたuserIdsを削除します。


```
curl -H 'Authorization: xxxxx' -X PATCH https://xxxxx.execute-api.ap-northeast-1.amazonaws.com/dev/tasks/{task_id}/remove --data '{"userIds": ["abcd1234","dcba4321"]}'
```

### Task_Done

タスクを完了済みに変更。
"done"をfalseからtrueに変更します。

```
curl -H 'Authorization: xxxxx' -X PATCH https://xxxxx.execute-api.ap-northeast-1.amazonaws.com/dev/tasks/{task_id}/done
```

### Task_Undone

タスクを未完に変更。
"done"をtrueらfalseに変更します。

```
curl -H 'Authorization: xxxxx' -X PATCH https://xxxxx.execute-api.ap-northeast-1.amazonaws.com/dev/tasks/{task_id}/undone
```

### Task_Delete

タスクの削除。
論理削除で実装しています。"deleteFlag"をfalseからtrueに変更します。

```
curl -H 'Authorization: xxxxx' -X DELETE https://xxxxx.execute-api.ap-northeast-1.amazonaws.com/dev/tasks/{task_id}
```

### Task_Users

タスクに参加するユーザー一覧を取得。

```
curl -H 'Authorization: xxxxx' https://xxxxx.execute-api.ap-northeast-1.amazonaws.com/dev/tasks/{task_id}/users
```

example output
```
{
  "statusCode": 200,
  "taskId": "abcd1234",
  "users": [
    {
      "phoneNumber": "08011112222",
      "updatedAt": "2019-12-05 12:21:50",
      "createdAt": "2019-12-05 12:21:50",
      "lastLogin": "2019-12-10T22:44:14",
      "id": "abcd1234",
      "email": "example1@foo.com",
      "name": "user1"
    }
  ]
}
```

### TaskList_Create

タスクリストの作成。

```
$ curl -H 'Authorization: xxxxx' -X POST https://https://xxxxx.execute-api.ap-northeast-1.amazonaws.com/dev/tasklists --data '{"name": "tasklist1", "description": "this is tasklist1"}'
```

required attributes
- name
- description

### TaskList_Update

タスクリストの更新。
更新対象のattributeは"name"および"description"です。

```
curl-H 'Authorization: xxxxx' -X PATCH https://xxxxx.execute-api.ap-northeast-1.amazonaws.com/dev/tasklists/{tasklist_id} --data '{"name": "tasklist2", "description": "This is tasklist2"}'
```

### TaskList_Delete

タスクリストの削除。
論理削除で実装しています。"deleteFlag"をfalseからtrueに変更します。

```
curl-H 'Authorization: xxxxx' -X DELETE https://xxxxx.execute-api.ap-northeast-1.amazonaws.com/dev/tasklists/{tasklists_id}
```

### TaskList_Index

タスクリストを全件取得。

```
curl -H 'Authorization: xxxxx' https://xxxxx.execute-api.ap-northeast-1.amazonaws.com/dev/tasklists
```

### TaskList_Tasks

タスクリストに属するタスクを全件取得。

```
curl -H 'Authorization: xxxxx' https://xxxxx.execute-api.ap-northeast-1.amazonaws.com/dev/tasklists/{tasklist_id}/tasks
```

example output
```
{
  "statusCode": 200,
  "taskList": "abcd1234",
  "tasks": [
    {
      "createdAt": "2019-12-05 12:12:33",
      "description": "This is task1",
      "id": "abcd1234",
      "name": "task1",
      "updatedAt": "2019-12-05 12:12:33",
      "userIds": [
        "abcd1234",
        "bcde2345",
        "cdef3456"
      ]
    }
  ]
}
```





