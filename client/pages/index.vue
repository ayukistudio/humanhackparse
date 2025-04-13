<script setup lang="ts">
import ProductCard from '~/components/ProductCard.vue'

interface Product {
	title: string
	price: number
	link: string
	article: string | null
	image?: string
	index?: number
}

interface ProductsData {
	ozon: Product[]
	wildberries: Product[]
	sbermegamarket: Product[]
}

const isLoading = useIsLoadingStoreProd()
const productsStore = useProductsStore()
const titleRef = ref('')

const products = computed(() => productsStore.getAllProducts())
const totalProducts = computed(() => productsStore.totalProducts)
const averagePrice = computed(() => productsStore.averagePrice)
const isStoreEmpty = computed(() => productsStore.isStoreEmpty())

const sortType = ref<'default' | 'priceAsc' | 'priceDesc'>('default')

const sortedProducts = computed(() => {
	const products = productsStore.getAllProducts()

	const sortedOzon = [...products.ozon]
	const sortedWildberries = [...products.wildberries]
	const sortedSbermegamarket = [...products.sbermegamarket]
	console.log(sortedWildberries)

	if (sortType.value === 'priceAsc') {
		sortedOzon.sort((a, b) => a.price - b.price)
		sortedWildberries.sort((a, b) => a.price - b.price)
		sortedSbermegamarket.sort((a, b) => a.price - b.price)
	} else if (sortType.value === 'priceDesc') {
		sortedOzon.sort((a, b) => b.price - a.price)
		sortedWildberries.sort((a, b) => b.price - a.price)
		sortedSbermegamarket.sort((a, b) => b.price - a.price)
	}

	return {
		ozon: sortedOzon,
		wildberries: sortedWildberries,
		sbermegamarket: sortedSbermegamarket
	}
})

const scrapeProducts = async () => {
	try {
		isLoading.set(true)
		productsStore.clearProducts()
		const products: ProductsData = await $fetch('/api/scrape-products', {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json'
			},
			body: {
				url: titleRef.value
			}
		})

		productsStore.setOzonProducts(products.ozon)
		productsStore.setWildberriesProducts(products.wildberries)
		productsStore.setSbermegamarketProducts(products.sbermegamarket)
		console.log(productsStore.getAllProducts())
		isLoading.set(false)
	} catch (error) {
		console.error(error)
		isLoading.set(false)
	}
}
</script>

<template>
	<div class="max-w-6xl h-full mx-auto">
		<form
			class="max-w-2xl mt-6 mx-auto"
			@submit.prevent="scrapeProducts"
		>
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
					v-model="titleRef"
					type="search"
					id="default-search"
					class="block w-full p-4 ps-10 pr-36 text-sm text-gray-900 border border-gray-300 rounded-lg bg-gray-50 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500"
					placeholder="Ищите товары, берите ссылки откуда угодно..."
					required
				/>
				<button
					type="submit"
					class="text-white absolute end-2.5 bottom-2.5 bg-blue-700 hover:bg-blue-800 focus:ring-4 focus:outline-none focus:ring-blue-300 font-medium rounded-lg text-sm px-4 py-2 dark:bg-blue-600 dark:hover:bg-blue-700 dark:focus:ring-blue-800"
				>
					Искать
				</button>
			</div>
		</form>
		<UtilsProdLoader v-if="isLoading.isLoading" />
		<div v-else>
			<h2
				v-if="!isStoreEmpty"
				class="text-2xl mt-6"
			>
				Найдено {{ totalProducts }} похожих товаров.
			</h2>
			<div
				v-if="!isStoreEmpty"
				class="max-w-[200px] mt-4"
			>
				<Select v-model="sortType">
					<SelectTrigger>
						<SelectValue placeholder="Сортировка по" />
					</SelectTrigger>

					<SelectContent>
						<SelectGroup>
							<SelectItem value="default"> умолчанию </SelectItem>
						</SelectGroup>
						<SelectGroup>
							<SelectItem value="priceAsc"> возрастанию цены </SelectItem>
						</SelectGroup>
						<SelectGroup>
							<SelectItem value="priceDesc"> убыванию цены </SelectItem>
						</SelectGroup>
					</SelectContent>
				</Select>
			</div>
			<div
				v-if="!isStoreEmpty"
				class="mt-6"
			>
				<Accordion
					type="single"
					collapsible
				>
					<AccordionItem value="item-1">
						<AccordionTrigger>Ozon</AccordionTrigger>
						<AccordionContent>
							<div class="grid grid-cols-4 gap-6">
								<ProductCard
									v-for="product in sortedProducts.ozon"
									:key="product.index"
									:link="product.link"
									:title="product.title"
									:price="product.price"
									:img="product.image"
								/>
							</div>
						</AccordionContent>
					</AccordionItem>
					<AccordionItem value="item-2">
						<AccordionTrigger>Sbermegamarket</AccordionTrigger>
						<AccordionContent>
							<div class="grid grid-cols-4 gap-6">
								<ProductCard
									v-for="product in sortedProducts.sbermegamarket"
									:key="product.index"
									:title="product.title"
									:price="product.price"
									:img="product.image"
								/>
							</div>
						</AccordionContent>
					</AccordionItem>
					<AccordionItem value="item-3">
						<AccordionTrigger>Wildberries</AccordionTrigger>
						<AccordionContent>
							<div class="grid md:grid-cols-4 gap-6">
								<ProductCard
									v-for="product in sortedProducts.wildberries"
									:key="product.index"
									:title="product.title"
									:price="product.price"
									:img="product.image"
								/>
							</div>
						</AccordionContent>
					</AccordionItem>
				</Accordion>
			</div>
		</div>
	</div>
</template>
