<template>
	<div class='max-w-7xl mx-auto'>
        <h2 class='text-2xl '>{{ prod.title }}</h2>
	<div class="chart-container mt-20 flex items-center">
        <img :src="prod.img" >
		<v-chart :option="chartOptions" autoresize />
	</div>
    </div>
</template>

<script setup>
import { DB } from '~/lib/appwrite'
import { COLLECTION_PRODUCTS, DB_ID } from '~/app.constants'
const route = useRoute()
const prod = ref('')
const price = prod.value.price

onMounted(async () => {
	const product = await DB.getDocument(DB_ID, COLLECTION_PRODUCTS, route.params.id)
    prod.value = product
	const data = await $fetch('/api/track-price', {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json'
		},
		body: {
			url: product.url,
			user_id: product.user_id
		}
	})

	console.log(data)
})
import VChart from 'vue-echarts';
import { use } from 'echarts/core';
import { CanvasRenderer } from 'echarts/renderers';
import { LineChart } from 'echarts/charts';
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent
} from 'echarts/components';
import { ref } from 'vue';

// Регистрируем компоненты ECharts
use([
  CanvasRenderer,
  LineChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent
]);

// Настройки графика
const chartOptions = ref({
  title: {
    text: 'График цен',
    left: 'center'
  },
  tooltip: {
    trigger: 'axis'
  },
  legend: {
    data: ['Цена'],
    top: 'bottom'
  },
  xAxis: {
    type: 'category',
    data: ['Апрель'],
    name: 'Месяцы'
  },
  yAxis: {
    type: 'value',
    name: 'Значение'
  },
  series: [
    {
      name: 'Цена',
      type: 'line',
      smooth: true,
      data: [prod.value.price || 3278],
      lineStyle: {
        color: '#42A5F5'
      },
      itemStyle: {
        color: '#42A5F5'
      }
    }
  ]
});
</script>

<style scoped>
.chart-container {
	position: relative;
	height: 400px;
	width: 100%;
}
</style>
