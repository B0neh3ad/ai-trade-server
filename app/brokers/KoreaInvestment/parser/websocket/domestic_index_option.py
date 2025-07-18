from dataclasses import dataclass

### 국내 지수옵션 ###

### 실시간 호가 (H0IOASP0) ###
@dataclass
class DomesticIndexOptionOrderbookResponse:
    shrn_iscd: str    #옵션 단축 종목코드
    bsop_hour: str    #영업 시간
    optn_askp1: str    #옵션 매도호가1
    optn_askp2: str    #옵션 매도호가2
    optn_askp3: str    #옵션 매도호가3
    optn_askp4: str    #옵션 매도호가4
    optn_askp5: str    #옵션 매도호가5
    optn_bidp1: str    #옵션 매수호가1
    optn_bidp2: str    #옵션 매수호가2
    optn_bidp3: str    #옵션 매수호가3
    optn_bidp4: str    #옵션 매수호가4
    optn_bidp5: str    #옵션 매수호가5
    askp_csnu1: str    #매도호가 건수1
    askp_csnu2: str    #매도호가 건수2
    askp_csnu3: str    #매도호가 건수3
    askp_csnu4: str    #매도호가 건수4
    askp_csnu5: str    #매도호가 건수5
    bidp_csnu1: str    #매수호가 건수1
    bidp_csnu2: str    #매수호가 건수2
    bidp_csnu3: str    #매수호가 건수3
    bidp_csnu4: str    #매수호가 건수4
    bidp_csnu5: str    #매수호가 건수5
    askp_rsqn1: str    #매도호가 잔량1
    askp_rsqn2: str    #매도호가 잔량2
    askp_rsqn3: str    #매도호가 잔량3
    askp_rsqn4: str    #매도호가 잔량4
    askp_rsqn5: str    #매도호가 잔량5
    bidp_rsqn1: str    #매수호가 잔량1
    bidp_rsqn2: str    #매수호가 잔량2
    bidp_rsqn3: str    #매수호가 잔량3
    bidp_rsqn4: str    #매수호가 잔량4
    bidp_rsqn5: str    #매수호가 잔량5
    total_askp_csnu: str    #총 매도호가 건수
    total_bidp_csnu: str    #총 매수호가 건수
    total_askp_rsqn: str    #총 매도호가 잔량
    total_bidp_rsqn: str    #총 매수호가 잔량
    total_askp_rsqn_icdc: str    #총 매도호가 잔량 증감
    total_bidp_rsqn_icdc: str    #총 매수호가 잔량 증감

### 실시간 체결가 (H0IOCNT0) ###
@dataclass
class DomesticIndexOptionExecutionResponse:
    shrn_iscd: str    #옵션 단축 종목코드
    bsop_hour: str    #영업 시간
    optn_prpr: str    #옵션 현재가
    prdy_vrss_sign: str    #전일 대비 부호
    optn_prdy_vrss: str    #옵션 전일 대비
    prdy_ctrt: str    #전일 대비율
    optn_oprc: str    #옵션 시가2
    optn_hgpr: str    #옵션 최고가
    optn_lwpr: str    #옵션 최저가
    last_cnqn: str    #최종 거래량
    acml_vol: str    #누적 거래량
    acml_tr_pbmn: str    #누적 거래 대금
    hts_thpr: str    #HTS 이론가
    hts_otst_stpl_qty: str    #HTS 미결제 약정 수량
    otst_stpl_qty_icdc: str    #미결제 약정 수량 증감
    oprc_hour: str    #시가 시간
    oprc_vrss_prpr_sign: str    #시가2 대비 현재가 부호
    oprc_vrss_nmix_prpr: str    #시가 대비 지수 현재가
    hgpr_hour: str    #최고가 시간
    hgpr_vrss_prpr_sign: str    #최고가 대비 현재가 부호
    hgpr_vrss_nmix_prpr: str    #최고가 대비 지수 현재가
    lwpr_hour: str    #최저가 시간
    lwpr_vrss_prpr_sign: str    #최저가 대비 현재가 부호
    lwpr_vrss_nmix_prpr: str    #최저가 대비 지수 현재가
    shnu_rate: str    #매수2 비율
    prmm_val: str    #프리미엄 값
    invl_val: str    #내재가치 값
    tmvl_val: str    #시간가치 값
    delta: str    #델타
    gama: str    #감마
    vega: str    #베가
    theta: str    #세타
    rho: str    #로우
    hts_ints_vltl: str    #HTS 내재 변동성
    esdg: str    #괴리도
    otst_stpl_rgbf_qty_icdc: str    #미결제 약정 직전 수량 증감
    thpr_basis: str    #이론 베이시스
    unas_hist_vltl: str    #역사적변동성
    cttr: str    #체결강도
    dprt: str    #괴리율
    mrkt_basis: str    #시장 베이시스
    optn_askp1: str    #옵션 매도호가1
    optn_bidp1: str    #옵션 매수호가1
    askp_rsqn1: str    #매도호가 잔량1
    bidp_rsqn1: str    #매수호가 잔량1
    seln_cntg_csnu: str    #매도 체결 건수
    shnu_cntg_csnu: str    #매수 체결 건수
    ntby_cntg_csnu: str    #순매수 체결 건수
    seln_cntg_smtn: str    #총 매도 수량
    shnu_cntg_smtn: str    #총 매수 수량
    total_askp_rsqn: str    #총 매도호가 잔량
    total_bidp_rsqn: str    #총 매수호가 잔량
    prdy_vol_vrss_acml_vol_rate: str    #전일 거래량 대비 등락율
    avrg_vltl: str    #평균 변동성
    dscs_lrqn_vol: str    #협의대량누적 거래량
    dynm_mxpr: str    #실시간상한가
    dynm_llam: str    #실시간하한가
    dynm_prc_limt_yn: str    #실시간가격제한구분

