-- MySQL dump 10.13  Distrib 8.0.39, for Win64 (x86_64)
--
-- Host: localhost    Database: happy
-- ------------------------------------------------------
-- Server version	8.0.39

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES UTF8MB4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `concept_sector`
--

DROP TABLE IF EXISTS `concept_sector`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `concept_sector` (
  `ts_code` varchar(255) NOT NULL COMMENT '概念板块代码',
  `name` varchar(255) NOT NULL COMMENT '概念板块名称',
  UNIQUE KEY `idx_concept_ts_code` (`ts_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `concept_sector_daily`
--

DROP TABLE IF EXISTS `concept_sector_daily`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `concept_sector_daily` (
  `ts_code` varchar(255) NOT NULL COMMENT 'TS指数代码',
  `name` varchar(255) NOT NULL COMMENT '指数名称',
  `trade_date` varchar(255) NOT NULL COMMENT '交易日',
  `close` float NOT NULL COMMENT '收盘点位',
  `open` float NOT NULL COMMENT '开盘点位',
  `high` float NOT NULL COMMENT '最高点位',
  `low` float NOT NULL COMMENT '最低点位',
  `pre_close` float NOT NULL COMMENT '昨日收盘点',
  `avg_price` float NOT NULL COMMENT '平均价',
  `price_change` float NOT NULL COMMENT '涨跌点位',
  `pct_change` float NOT NULL COMMENT '涨跌幅',
  `vol` float NOT NULL COMMENT '成交量',
  `turnover_rate` float NOT NULL COMMENT '换手率',
  `total_mv` float DEFAULT NULL COMMENT '总市值',
  `float_mv` float DEFAULT NULL COMMENT '流通市值',
  `ma_5` float DEFAULT NULL COMMENT '5日均线',
  `ma_10` float DEFAULT NULL COMMENT '10日均线',
  `ma_20` float DEFAULT NULL COMMENT '20日均线',
  `ma_60` float DEFAULT NULL COMMENT '60日均线',
  `boll_up` float DEFAULT NULL COMMENT 'boll-up',
  `boll_mid` float DEFAULT NULL COMMENT 'boll-mid',
  `boll_low` float DEFAULT NULL COMMENT 'boll-low',
  `kdj` float DEFAULT NULL COMMENT 'kdj',
  `boll` float DEFAULT NULL COMMENT 'boll',
  `macd` float DEFAULT NULL COMMENT 'MACD指标值',
  UNIQUE KEY `idx_concept_daily` (`ts_code`,`trade_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `concept_stock`
--

DROP TABLE IF EXISTS `concept_stock`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `concept_stock` (
  `sector_code` varchar(255) NOT NULL COMMENT '指数代码',
  `sector_name` varchar(255) NOT NULL COMMENT '指数名称',
  `stock_code` varchar(255) NOT NULL COMMENT '股票代码',
  `stokc_name` varchar(255) NOT NULL COMMENT '股票名称',
  `weight` float DEFAULT NULL COMMENT '权重(暂无)',
  `in_date` varchar(255) DEFAULT NULL COMMENT '纳入日期(暂无)',
  `out_date` varchar(255) DEFAULT NULL COMMENT '剔除日期(暂无)',
  `is_new` varchar(1) DEFAULT NULL COMMENT '是否最新Y是N否',
  UNIQUE KEY `idx_concept_stock` (`sector_code`,`stock_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `daily_data`
--

DROP TABLE IF EXISTS `daily_data`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `daily_data` (
  `id` int NOT NULL AUTO_INCREMENT,
  `stock_name` varchar(255) NOT NULL,
  `stock_code` varchar(20) NOT NULL,
  `trade_date` date NOT NULL,
  `low_price` decimal(10,2) NOT NULL,
  `high_price` decimal(10,2) NOT NULL,
  `open_price` decimal(10,2) NOT NULL,
  `close_price` decimal(10,2) NOT NULL,
  `turnover_amount` decimal(20,2) NOT NULL,
  `trading_volume` bigint NOT NULL,
  `turnover_rate` decimal(5,2) DEFAULT NULL,
  `price_change_rate` decimal(5,2) DEFAULT NULL,
  `previous_close_price` decimal(10,2) DEFAULT NULL,
  `is_limit_up` tinyint(1) DEFAULT NULL,
  `consecutive_limit_up_days` int DEFAULT NULL,
  `is_board_broken` tinyint(1) DEFAULT NULL,
  `call_auction_increase` decimal(5,2) DEFAULT NULL,
  `ma_5` decimal(10,2) DEFAULT NULL,
  `ma_10` decimal(10,2) DEFAULT NULL,
  `ma_20` decimal(10,2) DEFAULT NULL,
  `ma_60` decimal(10,2) DEFAULT NULL,
  `boll_low` decimal(10,2) DEFAULT NULL,
  `boll_mid` decimal(10,2) DEFAULT NULL,
  `boll_up` decimal(10,2) DEFAULT NULL,
  `kdj` decimal(10,2) DEFAULT NULL,
  `macd` decimal(10,2) DEFAULT NULL,
  `industry_sector` varchar(255) DEFAULT NULL,
  `concept_sector` varchar(255) DEFAULT NULL,
  `up_limit` float DEFAULT NULL,
  `down_limit` float DEFAULT NULL,
  `turnover_rate_f` float DEFAULT NULL,
  `volume_ratio` float DEFAULT NULL,
  `pe` float DEFAULT NULL,
  `pe_ttm` float DEFAULT NULL,
  `pb` float DEFAULT NULL,
  `ps` float DEFAULT NULL,
  `ps_ttm` float DEFAULT NULL,
  `dv_ratio` float DEFAULT NULL,
  `dv_ttm` float DEFAULT NULL,
  `total_share` float DEFAULT NULL,
  `float_share` float DEFAULT NULL,
  `free_share` float DEFAULT NULL,
  `total_mv` float DEFAULT NULL,
  `circ_mv` float DEFAULT NULL,
  `is_limit_down` tinyint(1) DEFAULT '0',
  PRIMARY KEY (`id`),
  UNIQUE KEY `idx_stock_date` (`stock_code`,`trade_date`),
  KEY `idx_daily_data_trade_date` (`trade_date`)
) ENGINE=InnoDB AUTO_INCREMENT=5619084 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `index_daily_data`
--

DROP TABLE IF EXISTS `index_daily_data`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `index_daily_data` (
  `ts_code` varchar(20) NOT NULL COMMENT 'TS指数代码',
  `trade_date` varchar(8) NOT NULL COMMENT '交易日',
  `close` float DEFAULT NULL COMMENT '收盘点位',
  `open` float DEFAULT NULL COMMENT '开盘点位',
  `high` float DEFAULT NULL COMMENT '最高点位',
  `low` float DEFAULT NULL COMMENT '最低点位',
  `pre_close` float DEFAULT NULL COMMENT '昨日收盘点',
  `price_change` float DEFAULT NULL COMMENT '涨跌点',
  `pct_chg` float DEFAULT NULL COMMENT '涨跌幅（%）',
  `vol` float DEFAULT NULL COMMENT '成交量（手）',
  `amount` float DEFAULT NULL COMMENT '成交额（千元）',
  `ma_5` float DEFAULT NULL COMMENT '5日均线',
  `ma_10` float DEFAULT NULL COMMENT '10日均线',
  `ma_20` float DEFAULT NULL COMMENT '20日均线',
  `ma_60` float DEFAULT NULL COMMENT '60日均线',
  `boll_up` float DEFAULT NULL COMMENT 'boll-up',
  `boll_mid` float DEFAULT NULL COMMENT 'boll-mid',
  `boll_low` float DEFAULT NULL COMMENT 'boll-low',
  `kdj` float DEFAULT NULL COMMENT 'kdj',
  `macd` float DEFAULT NULL COMMENT 'macd',
  UNIQUE KEY `idx_ts_code_trade_date` (`ts_code`,`trade_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='指数日线数据表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `index_info`
--

DROP TABLE IF EXISTS `index_info`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `index_info` (
  `ts_code` varchar(20) NOT NULL COMMENT '指数代码',
  `name` varchar(100) DEFAULT NULL COMMENT '指数名称',
  UNIQUE KEY `idx_ts_code` (`ts_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='指数信息表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `industry_sector`
--

DROP TABLE IF EXISTS `industry_sector`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `industry_sector` (
  `ts_code` varchar(255) NOT NULL COMMENT '行业板块代码',
  `name` varchar(255) NOT NULL COMMENT '行业板块名称',
  UNIQUE KEY `idx_industry_ts_code` (`ts_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `industry_sector_daily`
--

DROP TABLE IF EXISTS `industry_sector_daily`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `industry_sector_daily` (
  `ts_code` varchar(255) NOT NULL COMMENT 'TS指数代码',
  `name` varchar(255) NOT NULL COMMENT '指数名称',
  `trade_date` varchar(255) NOT NULL COMMENT '交易日',
  `close` float NOT NULL COMMENT '收盘点位',
  `open` float NOT NULL COMMENT '开盘点位',
  `high` float NOT NULL COMMENT '最高点位',
  `low` float NOT NULL COMMENT '最低点位',
  `pre_close` float NOT NULL COMMENT '昨日收盘点',
  `avg_price` float NOT NULL COMMENT '平均价',
  `price_change` float NOT NULL COMMENT '涨跌点位',
  `pct_change` float NOT NULL COMMENT '涨跌幅',
  `vol` float NOT NULL COMMENT '成交量',
  `turnover_rate` float NOT NULL COMMENT '换手率',
  `total_mv` float DEFAULT NULL COMMENT '总市值',
  `float_mv` float DEFAULT NULL COMMENT '流通市值',
  `ma_5` float DEFAULT NULL COMMENT '5日均线',
  `ma_10` float DEFAULT NULL COMMENT '10日均线',
  `ma_20` float DEFAULT NULL COMMENT '20日均线',
  `ma_60` float DEFAULT NULL COMMENT '60日均线',
  `boll_up` float DEFAULT NULL COMMENT 'boll-up',
  `boll_mid` float DEFAULT NULL COMMENT 'boll-mid',
  `boll_low` float DEFAULT NULL COMMENT 'boll-low',
  `kdj` float DEFAULT NULL COMMENT 'kdj',
  `boll` float DEFAULT NULL COMMENT 'boll',
  `macd` float DEFAULT NULL COMMENT 'MACD指标值',
  UNIQUE KEY `idx_industry_daily` (`ts_code`,`trade_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `industry_stock`
--

DROP TABLE IF EXISTS `industry_stock`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `industry_stock` (
  `sector_code` varchar(255) NOT NULL COMMENT '指数代码',
  `sector_name` varchar(255) NOT NULL COMMENT '指数名称',
  `stock_code` varchar(255) NOT NULL COMMENT '股票代码',
  `stokc_name` varchar(255) NOT NULL COMMENT '股票名称',
  `weight` float DEFAULT NULL COMMENT '权重(暂无)',
  `in_date` varchar(255) DEFAULT NULL COMMENT '纳入日期(暂无)',
  `out_date` varchar(255) DEFAULT NULL COMMENT '剔除日期(暂无)',
  `is_new` varchar(1) DEFAULT NULL COMMENT '是否最新Y是N否',
  UNIQUE KEY `idx_industry_stock` (`sector_code`,`stock_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `limit_stocks`
--

DROP TABLE IF EXISTS `limit_stocks`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `limit_stocks` (
  `trade_date` varchar(20) NOT NULL COMMENT '交易日期',
  `ts_code` varchar(20) NOT NULL COMMENT '股票代码',
  `industry` varchar(4096) NOT NULL COMMENT '所属行业',
  `concept` varchar(4096) NOT NULL COMMENT '所属概念',
  `market_type` varchar(20) NOT NULL COMMENT '股票类型：HS沪深主板、GEM创业板、STAR科创板',
  `name` varchar(100) NOT NULL COMMENT '股票名称',
  `close` float DEFAULT NULL COMMENT '收盘价',
  `pct_chg` float DEFAULT NULL COMMENT '涨跌幅',
  `amount` float DEFAULT NULL COMMENT '成交额',
  `limit_amount` float DEFAULT NULL COMMENT '板上成交金额(涨停无此数据)',
  `float_mv` float DEFAULT NULL COMMENT '流通市值',
  `total_mv` float DEFAULT NULL COMMENT '总市值',
  `turnover_ratio` float DEFAULT NULL COMMENT '换手率',
  `fd_amount` float DEFAULT NULL COMMENT '封单金额',
  `first_time` varchar(20) DEFAULT NULL COMMENT '首次封板时间（跌停无此数据）',
  `last_time` varchar(20) DEFAULT NULL COMMENT '最后封板时间',
  `open_times` int DEFAULT NULL COMMENT '炸板次数(跌停为开板次数)',
  `up_stat` varchar(20) DEFAULT NULL COMMENT '涨停统计（N/T T天有N次涨停）',
  `limit_times` int DEFAULT NULL COMMENT '连板数',
  `limit_type` varchar(1) DEFAULT NULL COMMENT 'D跌停U涨停Z炸板',
  UNIQUE KEY `idx_trade_date_ts_code` (`trade_date`,`ts_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='涨跌停股票表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `stock`
--

DROP TABLE IF EXISTS `stock`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `stock` (
  `id` int NOT NULL AUTO_INCREMENT,
  `stock_code` varchar(20) NOT NULL,
  `stock_name` varchar(255) NOT NULL,
  `area` varchar(50) DEFAULT NULL,
  `industry` varchar(100) DEFAULT NULL,
  `concept` varchar(255) DEFAULT NULL,
  `exchange_code` varchar(10) DEFAULT NULL,
  `is_st` tinyint(1) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=10793 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-02-14 17:26:30
