<script setup lang="ts">
import type { IColumn, ICard } from '~/components/kanban/kanban.types'
import { useKanbanQuery } from '~/components/kanban/useKanbanQuery'
import dayjs from 'dayjs'
import type { EnumStatus } from '~/types/deals.types'
import { useMutation } from '@tanstack/vue-query'
import { DB } from '~/lib/appwrite'
import { COLLECTION_DEALS, DB_ID } from '~/app.constants'

const dragCardRef = ref<ICard | null>(null)
const sourceColumnRef = ref<IColumn | null>(null)

const { data, isLoading, refetch } = useKanbanQuery()

type TypeMutationVariables = {
	docId: string
	status?: EnumStatus
}

const { mutate } = useMutation({
	mutationKey: ['move card'],
	mutationFn: ({ docId, status }: TypeMutationVariables) =>
		DB.updateDocument(DB_ID, COLLECTION_DEALS, docId, {
			status
		}),
	onSuccess: () => {
		refetch()
	}
})

function handleDragStart(card: ICard, column: IColumn) {
	dragCardRef.value = card
	sourceColumnRef.value = column
}

function handleDragOver(event: DragEvent) {
	event.preventDefault()
}

function handleDrop(targetColumn: IColumn) {
	if (dragCardRef.value && sourceColumnRef.value) {
		mutate({ docId: dragCardRef.value.id, status: targetColumn.id })
	}
}
</script>

<template>
	<div class="max-w-7xl mx-auto">

		<form class="max-w-2xl mt-6 mx-auto">
			<label
				for="default-search"
				class="mb-2 text-sm font-medium text-gray-900 sr-only dark:text-white"
				>Search</label
			>
			<div class="relative">
				<div class="absolute inset-y-0 start-0 flex items-center ps-3 pointer-events-none">
					<svg
						class="w-4 h-4 text-gray-500 dark:text-gray-400"
						aria-hidden="true"
						xmlns="http://www.w3.org/2000/svg"
						fill="none"
						viewBox="0 0 20 20"
					>
						<path
							stroke="currentColor"
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="m19 19-4-4m0-7A7 7 0 1 1 1 8a7 7 0 0 1 14 0Z"
						/>
					</svg>
				</div>
				<input
					type="search"
					id="default-search"
					class="block w-full p-4 ps-10 text-sm text-gray-900 border border-gray-300 rounded-lg bg-gray-50 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500"
					placeholder="Search Mockups, Logos..."
					required
				/>
				<button
					type="submit"
					class="text-white absolute end-2.5 bottom-2.5 bg-blue-700 hover:bg-blue-800 focus:ring-4 focus:outline-none focus:ring-blue-300 font-medium rounded-lg text-sm px-4 py-2 dark:bg-blue-600 dark:hover:bg-blue-700 dark:focus:ring-blue-800"
				>
					Search
				</button>
			</div>
		</form>
	</div>
</template>
