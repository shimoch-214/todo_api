## todo-api

serverless frameworkを利用した簡易的なtodoアプリ用のapiです。

- 構成
  - AWS APIGateway
  - AWS DynamoDB
  - AWS Lambda

- 実装
  - serverless framework v1.58
  - python 3.6

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

## Usage

### User_Create

ユーザーの作成。

```
$ curl -X POST https://https://xxxxx.execute-api.ap-northeast-1.amazonaws.com/dev/users --data '{"name": "user1", "email": "example1@foo.com", "phoneNumber": "08011112222"}'
```

required attribute
- name
- email
- phoneNumber

### User_Update

ユーザーの更新。
更新対象のattributeは"name", "email", および"phoneNumber"です。

```
curl -X PATCH https://xxxxx.execute-api.ap-northeast-1.amazonaws.com/dev/users/{user_id} --data '{"name": "user2", "email": "example2@foo.com"}'
```


### User_Delete

ユーザーの削除。
論理削除で実装しています。"deleteFlag"をfalseからtrueに変更します。また参加しいるtaskの"userIds"より自身のidを削除します。

```
curl -X DELETE https://xxxxx.execute-api.ap-northeast-1.amazonaws.com/dev/users/{user_id}
```

### User_tasks_tasklists

ユーザーの参加するtask一覧およびtasklist一覧を取得。

```
curl https://xxxxx.execute-api.ap-northeast-1.amazonaws.com/dev/users/{user_id}/tasks_tasklists
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
$ curl -X POST https://https://xxxxx.execute-api.ap-northeast-1.amazonaws.com/dev/tasks --data '{"name": "task1", "description": "this is task1"}'
```

required attribute
- name
- description
- userIds(option)

### Task_Update

タスクの更新。
更新対象のattributeは"name"および"description"です。

```
curl -X PATCH https://xxxxx.execute-api.ap-northeast-1.amazonaws.com/dev/tasks/{task_id} --data '{"name": "task2", "description": "This is task2"}'
```

### Task_Add

タスクにユーザーを追加。
"userIds"(array)に与えられたuserIdsを追加します。

```
curl -X PATCH https://xxxxx.execute-api.ap-northeast-1.amazonaws.com/dev/tasks/{task_id}/add --data '{"userIds": ["abcd1234","dcba4321"]}'
```

### Task_Remove

タスクからユーザーを削除。
userIds"(array)から与えられたuserIdsを削除します。


```
curl -X PATCH https://xxxxx.execute-api.ap-northeast-1.amazonaws.com/dev/tasks/{task_id}/remove --data '{"userIds": ["abcd1234","dcba4321"]}'
```

### Task_Done

タスクを完了済みに変更。
"done"をfalseからtrueに変更します。

```
curl -X PATCH https://xxxxx.execute-api.ap-northeast-1.amazonaws.com/dev/tasks/{task_id}/done
```

### Task_Undone

タスクを未完に変更。
"done"をtrueらfalseに変更します。

```
curl -X PATCH https://xxxxx.execute-api.ap-northeast-1.amazonaws.com/dev/tasks/{task_id}/undone
```

### Task_Delete

タスクの削除。
論理削除で実装しています。"deleteFlag"をfalseからtrueに変更します。

```
curl -X DELETE https://xxxxx.execute-api.ap-northeast-1.amazonaws.com/dev/tasks/{task_id}
```

### Task_Users

タスクに参加するユーザー一覧を取得。

```
curl https://xxxxx.execute-api.ap-northeast-1.amazonaws.com/dev/tasks/{task_id}/users
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
$ curl -X POST https://https://xxxxx.execute-api.ap-northeast-1.amazonaws.com/dev/tasklists --data '{"name": "tasklist1", "description": "this is tasklist1"}'
```

required attribute
- name
- description

### TaskList_Update

タスクリストの更新。
更新対象のattributeは"name"および"description"です。

```
curl -X PATCH https://xxxxx.execute-api.ap-northeast-1.amazonaws.com/dev/tasklists/{tasklist_id} --data '{"name": "tasklist2", "description": "This is tasklist2"}'
```

### TaskList_Delete

タスクリストの削除。
論理削除で実装しています。"deleteFlag"をfalseからtrueに変更します。

```
curl -X DELETE https://xxxxx.execute-api.ap-northeast-1.amazonaws.com/dev/tasklists/{tasklists_id}
```

### TaskList_Index

タスクリストを全件取得。

```
curl https://xxxxx.execute-api.ap-northeast-1.amazonaws.com/dev/tasklists
```

### TaskList_Tasks

タスクリストに属するタスクを全件取得。

```
curl https://xxxxx.execute-api.ap-northeast-1.amazonaws.com/dev/tasklists/{tasklist_id}/tasks
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





