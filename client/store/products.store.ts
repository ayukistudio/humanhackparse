// stores/products.ts
import { defineStore } from 'pinia'

interface Product {
	title: string
	price: number
	link: string
	article: string | null
	image?: string
	index?: number
}

interface ProductsState {
	ozonProducts: Product[]
	wildberriesProducts: Product[]
	sbermegamarketProducts: Product[]
}

export const useProductsStore = defineStore('products', {
	state: (): ProductsState => ({
		ozonProducts: [],
		wildberriesProducts: [],
		sbermegamarketProducts: []
	}),

	actions: {
		// Установка данных для Ozon
		setOzonProducts(products: any[]): void {
			this.ozonProducts = products.map(product => ({
				title: product.title,
				price: product.price,
				link: product.link,
				image: product.image,
				article: product.article
			}))
		},

		// Установка данных для Wildberries
		setWildberriesProducts(products: any[]): void {
			this.wildberriesProducts = products.map(product => ({
				title: product.title,
				price: product.price,
				link: product.link,
				article: product.article,
				index: product.index
			}))
		},

		// Установка данных для SberMegaMarket
		setSbermegamarketProducts(products: any[]): void {
			this.sbermegamarketProducts = products.map(product => ({
				title: product.title,
				price: product.price,
				link: product.link,
				article: product.article,
				image: product.image
			}))
		},

		// Получение всех продуктов
		getAllProducts(): { ozon: Product[]; wildberries: Product[]; sbermegamarket: Product[] } {
			return {
				ozon: this.ozonProducts,
				wildberries: this.wildberriesProducts,
				sbermegamarket: this.sbermegamarketProducts
			}
		},
        getProdSidebar(): Product[] {
            return {
                ...this.ozonProducts,
                ...this.wildberriesProducts,
                ...this.sbermegamarketProducts
            }
        },

		isStoreEmpty(): boolean {
			return this.ozonProducts.length === 0 && this.wildberriesProducts.length === 0 && this.sbermegamarketProducts.length === 0
		},

		// Очистка данных
		clearProducts(): void {
			this.ozonProducts = []
			this.wildberriesProducts = []
			this.sbermegamarketProducts = []
		},

		// Поиск продукта по артикулу
		findProductByArticle(article: string): Product[] {
			return [
				...this.ozonProducts.filter(p => p.article === article),
				...this.wildberriesProducts.filter(p => p.article === article),
				...this.sbermegamarketProducts.filter(p => p.article === article)
			]
		}
	},

	getters: {
		// Получение общего количества продуктов
		totalProducts: (state: ProductsState): number => {
			return state.ozonProducts.length + state.wildberriesProducts.length + state.sbermegamarketProducts.length
		},

		// Средняя цена продуктов
		averagePrice: (state: ProductsState): number => {
			const allProducts = [
                ...state.ozonProducts,
                ...state.wildberriesProducts,
                ...state.sbermegamarketProducts
              ]
              if (!allProducts.length) return 0
        
              // Фильтруем только продукты с валидными ценами
              const validProducts = allProducts.filter(product => 
                typeof product.price === 'number' && !isNaN(product.price)
              )
              if (!validProducts.length) return 0
        
              const total = validProducts.reduce((sum, product) => sum + product.price, 0)
              return Number((total / validProducts.length).toFixed(2))
		},

		// Фильтрация продуктов по ценовому диапазону
		productsByPriceRange:
			(state: ProductsState) =>
			(
				minPrice: number,
				maxPrice: number
			): {
				ozon: Product[]
				wildberries: Product[]
				sbermegamarket: Product[]
			} => {
				return {
					ozon: state.ozonProducts.filter(p => p.price >= minPrice && p.price <= maxPrice),
					wildberries: state.wildberriesProducts.filter(p => p.price >= minPrice && p.price <= maxPrice),
					sbermegamarket: state.sbermegamarketProducts.filter(p => p.price >= minPrice && p.price <= maxPrice)
				}
			}
	}
})
