<template>
	<Card
		v-if="title && price"
		class="w-[270px] h-lg overflow-hidden relative pb-16"
	>
		<NuxtLink :to="link">
			<img
			v-if="img"
			:src="img"
			class="w-full h-[250px]"
			alt="Image"
		/>
		<img
			v-else
			src="~/assets/placeholder.jpg"
			alt=""
		/>
		</NuxtLink>
		<CardHeader>
			<CardTitle>{{ title }}</CardTitle>
		</CardHeader>
		<CardContent class="flex absolute bottom-0 gap-8 justify-between w-full items-center">
			<p>{{ price }} ₽</p>
			<Button
				@click="addProduct(img, title, price, link)"
				class="right-0"
				>+</Button
			>
		</CardContent>
	</Card>
</template>

<script setup>
import { COLLECTION_PRODUCTS, DB_ID } from '~/app.constants'
import { DB } from '~/lib/appwrite'
const productStore = useProductStore()
const authStore = useAuthStore()

const props = defineProps({
	title: String,
	price: Number,
	img: String,
	link: String
})

const addProduct = async (img, title, price, link) => {
	await DB.createDocument(DB_ID, COLLECTION_PRODUCTS,  'unique()', { user_id: authStore.user_id, img: img, title: title, price: Number(price), url: link })
	await productStore.fetchProducts()
}
</script>
