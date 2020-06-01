For existing endpoint `/v4/pipeline-item`, ensure that contact and sector segment are set to nestedRelatedFields so that we get the contact name and sector segment alongside with their ids. These fields are optional so no extra logic is present in this change.

previous response:
```
...
"contact": "uuid",
"sector": "uuid",
...
```

current response:
```
...
"contact": {
  "id": "uuid",
  "name": "name"
},
"sector": {
  "id": "uuid",
  "segment": "segment"
},
...
```