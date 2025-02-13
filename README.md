# my-chat

## Frontend

run: `npm run dev`

installing components:
https://ui.shadcn.com/docs/installation/next

npx shadcn@latest add button
npx shadcn@latest add input
npx shadcn@latest add label
npx shadcn@latest add card
npx shadcn@latest add skeleton
npx shadcn@latest add avatar
npx shadcn@latest add textarea
npx shadcn@latest add separator
npx shadcn@latest add label 
npx shadcn@latest add dialog
npx shadcn@latest add sidebar-07
npx shadcn@latest add copy-button
npx shadcn@latest add switch


npm install remark-gfm rehype-raw
npm install react-markdown remark-gfm rehype-raw prismjs react-syntax-highlighter

components:
https://ui.shadcn.com/docs/components/dialog


npx shadcn@latest add https://shadcn-chatbot-kit.vercel.app/r/markdown-renderer.json

## Backend

run: `uvicorn main:app --reload`


## Todos

- [ ] multi-page
- [x] login functionality
- [ ] display li/ul correctly within messages
- [x] FIX width of messages when Web Sufer -> problem je v PRE/CODE
- [x] closing the session (event source)


## Run docker locally

```bash
docker build --tag fastapi-demo .
```

```bash 
docker run --detach --publish 3100:3100 fastapi-demo
```


## Manual Deploy to Azure


```bash
az containerapp up --resource-group rg-autogen-demos --name autogen-demo-be2  --ingress external --target-port 3100 --source . --env-vars "AZURE_OPENAI_ENDPOINT=https://aoai-eastus-mma-cdn.openai.azure.com/" "POOL_MANAGEMENT_ENDPOINT=https://swedencentral.dynamicsessions.io/subscriptions/de281c5e-5d60-4fc1-b905-c91caf45e624/resourceGroups/rg-dream-team/sessionPools/sessionpool"

```

<!-- manged identity
autogen-demo-mi

```bash
az containerapp up --resource-group rg-autogen-demos --name autogen-demo-be --ingress external --target-port 3100 --source . --assign-identity autogen-demo-mi
``` -->


## Cosmos DB Setting rights

```bash

resourceGroupName='rg-ai'
accountName='mma-cosmosdb'
readOnlyRoleDefinitionId='00000000-0000-0000-0000-000000000002' # This is the ID of the Cosmos DB Built-in Data contributor role definition
principalId=da6cb168-9a34-4ebe-9df8-638971852649 # This is the object ID of the managed identity.
az cosmosdb sql role assignment create --account-name $accountName --resource-group $resourceGroupName --scope "/" --principal-id $principalId --role-definition-id $readOnlyRoleDefinitionId
```