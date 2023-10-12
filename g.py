CREDIT_LINE_QUERY = '''
with base_data as (
select 
partner_loan_id, customer_name,
loan_start_date	,loan_closed_date,
maturity_date,	tenure	,interest_rate,
hurdle_rate,	product_code,	interest_type,
credit_limit,	loan_amount,finance_pos,
finance_overdue_principal,
CASE WHEN finance_loan_status IN ('closed', 'fldg_triggered', 'fldg_settled', 'written_off', 'cancelled') THEN 0 ELSE finance_interest_outstanding END AS finance_interest_outstanding,
CASE WHEN finance_loan_status IN ('closed', 'fldg_triggered', 'fldg_settled', 'written_off', 'cancelled') THEN 0 ELSE finance_interest_accrued_and_due END AS finance_interest_accrued_and_due,
CASE WHEN finance_loan_status IN ('closed', 'fldg_triggered', 'fldg_settled', 'written_off', 'cancelled') OR (as_on_date >= write_off_date) OR (as_on_date >= fldg_final_settlement_date) THEN 0 ELSE
(finance_interest_outstanding - finance_interest_accrued_and_due) END AS finance_interest_accrued_but_not_due,
finance_total_overdue,
'NA' AS excess_advance,
restructured_flag,restructured_date,
finance_dpd,
CASE WHEN finance_dpd = 0 THEN 'Bucket Current'
     WHEN finance_dpd < 31 THEN 'Bucket 1-30'
     WHEN finance_dpd < 61 THEN 'Bucket 31-60'
     WHEN finance_dpd < 91 THEN 'Bucket 61-90'
     WHEN finance_dpd < 121 THEN 'Bucket 91-120'
     WHEN finance_dpd < 151 THEN 'Bucket 121-150'
     WHEN finance_dpd < 181 THEN 'Bucket 151-180'
     ELSE 'Bucket 180+' END AS finance_dpd_bucket,
moratorium_loan_indicator,state_name,
loan_ticket,partner_code,
CASE WHEN fldg_principal_settled > 0 THEN fldg_principal_settled
     ELSE 0 END AS fldg_settled,
finance_loan_status,fldg_final_settlement_date,ucic,
credit_id,npa_tag,
finance_pos*interest_rate AS finance_pos_interest_rate,
finance_pos*hurdle_rate AS finance_pos_hurdle_rate,
finance_pos*tenure AS finance_pos_tenure,
CASE WHEN product_code in ('UDC') THEN 'SME'
     WHEN product_code in ('MTC','ESC','CRC') THEN 'Consumer' END as loan_type,
'Retail' AS partner_type,
processing_fees,
total_interest_due,
as_on_date,ksf_loan_id,
loan_status,loan_disbursal_date,
interest_rate_frequency,
Net_disbursed_amount,
bpi_due,due_date,principal_due,interest_due,
instalment_due,	
overdue_principal,interest_accrued_not_due,
interest_accrued_and_due,
interest_outstanding,ksf_interest_outstanding,
ksf_interest_accrued_and_due,
ksf_bpi_due,cumulative_principal_due,
cumulative_principal_paid,overdue_interest,
cumulative_interest_due,cumulative_interest_paid,
loan_overdue,dpd_days,
principal_outstanding,
parent_restructured_loan_indicator,snapshot_date,	
write_off_date,state,stage,partner_loan_status,
current_fldg_state,los_app_id,
created_date,finance_ksf_interest_outstanding,
finance_ksf_interest_accrued_and_due,	
finance_cumulative_overdue_principal,
finance_cumulative_overdue_interest


FROM (SELECT DISTINCT
*,
CASE WHEN ((cumulative_interest_due - cumulative_interest_paid) < 0) or (as_on_date >= write_off_date) OR (as_on_date >= fldg_final_settlement_date)  THEN 0
ELSE (cumulative_interest_due - cumulative_interest_paid) END as finance_interest_accrued_and_due,
CASE WHEN (as_on_date >= write_off_date) OR (as_on_date >= fldg_final_settlement_date) THEN 0 
ELSE dpd_days
END AS finance_dpd,
CASE WHEN (as_on_date >= write_off_date) OR (as_on_date >= fldg_final_settlement_date) THEN 0 
ELSE principal_outstanding
END AS finance_pos,
CASE WHEN (as_on_date >= write_off_date) OR (as_on_date >= fldg_final_settlement_date) THEN 0
ELSE overdue_principal
END AS finance_overdue_principal,
CASE WHEN (as_on_date >= write_off_date) OR (as_on_date >= fldg_final_settlement_date) THEN 0
ELSE interest_outstanding
END AS finance_interest_outstanding,
CASE WHEN (as_on_date >= write_off_date) OR (as_on_date >= fldg_final_settlement_date) THEN 0
ELSE ksf_interest_outstanding
END AS finance_ksf_interest_outstanding,
CASE WHEN (as_on_date >= write_off_date) OR (as_on_date >= fldg_final_settlement_date) THEN 0
ELSE ksf_interest_accrued_and_due
END AS finance_ksf_interest_accrued_and_due,
CASE WHEN (as_on_date >= write_off_date) OR (as_on_date >= fldg_final_settlement_date) THEN 0
ELSE overdue_principal
END AS finance_cumulative_overdue_principal,
CASE WHEN (as_on_date >= write_off_date) OR (as_on_date >= fldg_final_settlement_date) THEN 0 
ELSE overdue_interest
END AS finance_cumulative_overdue_interest,
CASE WHEN (as_on_date >= write_off_date) OR (as_on_date >= fldg_final_settlement_date) THEN 0 
ELSE loan_overdue
END AS finance_total_overdue,
CASE WHEN (parent_restructured_loan_indicator = TRUE) OR (child_restructured_loan_indicator = TRUE) THEN 'Y'
ELSE 'N'
END AS restructured_flag,

CASE 
WHEN (child_restructured_loan_indicator = TRUE ) THEN loan_start_date
WHEN (parent_restructured_loan_indicator = TRUE ) THEN loan_closed_date
ELSE '-'
END AS restructured_date

FROM(
SELECT
        dpd.as_on_date,
        COALESCE(lm.credit_id, cm.partner_app_id) as credit_id,
       dpd.partner_loan_id,
       lm.partner_code,
        lm.los_loan_booking_id AS ksf_loan_id,
       fm.product_code,
       cm.customer_name,
       fm.loan_amount,
       CASE WHEN fm.loan_amount < 70000 THEN  '<INR 70K'
            WHEN fm.loan_amount < 700000 THEN  '<INR 700K'
            WHEN fm.loan_amount < 7000000 THEN  '<INR 7mn'
            ELSE '>INR 7mn' END AS loan_ticket,
       CASE WHEN fm.loan_start_date = '<NA>' THEN replace(fm.loan_start_date, '<NA>', null) 
       ELSE fm.loan_start_date END AS loan_start_date,
       CASE WHEN fm.maturity_date = '<NA>' THEN replace(fm.maturity_date, '<NA>', null) 
       ELSE fm.maturity_date END AS maturity_date,
       fm.vcal_loan_status as loan_status,
       fm.tenure,
       fm.interest_rate,
       fm.interest_type,
        CASE WHEN disbursement.loan_disbursal_date = '<NA>' THEN replace(disbursement.loan_disbursal_date, '<NA>', null) 
       ELSE disbursement.loan_disbursal_date END AS loan_disbursal_date,
        CASE WHEN fm.loan_closed_date = '<NA>' THEN replace(fm.loan_closed_date, '<NA>', null) 
       ELSE fm.loan_closed_date END AS loan_closed_date,
       fm.interest_rate_frequency,
       disbursement.amount_disbursed as Net_disbursed_amount,
       disbursement.processing_fees as processing_fees,
       loan_book_summary.loan_interest_due as total_interest_due,
       fm.vcal_bpi AS bpi_due,
        CASE WHEN fs.due_date = '<NA>' THEN replace(fs.due_date, '<NA>', null) 
       ELSE fs.due_date END AS due_date,
       fs.principal_due AS principal_due,
       fs.interest_due AS interest_due,
       fs.instalment_due AS instalment_due,
       ls.loan_interest_accrued_not_due as interest_accrued_not_due,
       ls.loan_interest_overdue AS interest_accrued_and_due,
       ls.loan_interest_outstanding AS interest_outstanding,
       ls.ksf_loan_interest_outstanding AS ksf_interest_outstanding,
       ls.ksf_loan_interest_overdue AS ksf_interest_accrued_and_due,
       ls.ksf_bpi_due,
       ls.hurdle_rate,
       dpd.cumulative_principal_due,
       dpd.cumulative_principal_paid,
       dpd.overdue_principal AS overdue_principal,
       dpd.overdue_interest as overdue_interest,
       dpd.cumulative_interest_due,
       dpd.cumulative_interest_paid,
       ls.loan_overdue as loan_overdue,
       dpd.dpd_days,
       pos.outstanding_balance          AS principal_outstanding,
       fm.parent_restructured_loan_indicator,
       fm.child_restructured_loan_indicator,
       CASE WHEN fm.loan_moratorium_indicator = TRUE THEN 'Y'
        ELSE 'N'
       END AS moratorium_loan_indicator,
       fm.snapshot_date,
       mr.finance_loan_status,
       wo.write_off_date,
              CASE WHEN fm.loan_state = 'waive_off_settled' THEN 'waive_off'
              WHEN wo.state is null THEN 'Standard'
        ELSE wo.state
        END AS state,
        CASE WHEN fm.loan_status = 'closed' THEN 'Settled'
            WHEN (wo.stage = 'write_off') OR (wo.state = 'waive_off') THEN 'WriteOff'
            WHEN npa.npa_tag = '1' THEN 'NPA' 
            ELSE 'Standard'
        END AS stage,
        CASE WHEN npa.npa_tag = '1' THEN '1'
            ELSE '0' END AS npa_tag,
fm.loan_status AS partner_loan_status,
                fldg.current_fldg_state,
                fldg.fldg_final_settlement_date,
                fldg.fldg_principal_settled,
        cm.customer_id as ucic,
        sm.state_name ,
        cm.los_app_id as los_app_id,
        CASE WHEN fm.credit_limit is not NULL THEN CAST(fm.credit_limit AS VARCHAR)
        ELSE CAST(cm.line_approved  AS VARCHAR) END as credit_limit,
        cm.sanction_date as sanction_date,
        cm.expiry_date as expiry_date,
       CURRENT_DATE                     AS created_date
FROM   (SELECT dpd_tmp.partner_loan_id,
                dpd_tmp.as_on_date,
               dpd_tmp.overdue_principal,
               dpd_tmp.cumulative_principal_due,
               dpd_tmp.cumulative_principal_paid,
               dpd_tmp.overdue_interest,
               dpd_tmp.cumulative_interest_due,
               dpd_tmp.cumulative_interest_paid,
               dpd_tmp.dpd_days
               FROM
            (SELECT dpd.partner_loan_id,
                dpd.as_on_date,
               dpd.overdue_principal,
               dpd.cumulative_principal_due,
               dpd.cumulative_principal_paid,
               dpd.overdue_interest,
               dpd.cumulative_interest_due,
               dpd.cumulative_interest_paid,
               dpd.dpd_days,
               1 as rnk
        FROM   {target_database_name}.daily_dpd AS dpd
        WHERE  dpd.product_code = '{product_code}'
               AND dpd.snapshot_date = '{snapshot_date}'
               AND dpd.created_at_date = (SELECT Max(created_at_date)
                                          FROM
                   {target_database_name}.daily_dpd
                   WHERE  product_code = '{product_code}'
                    AND snapshot_date = '{snapshot_date}')
               AND dpd.as_on_date = '{snapshot_date}') AS dpd_tmp
        WHERE dpd_tmp.rnk = 1
        ) AS dpd
       LEFT JOIN (SELECT pos.partner_loan_id,
                         pos.date,
                         pos.outstanding_balance
                  FROM   {target_database_name}.monthly_pos AS pos
                  WHERE  pos.product_code = '{product_code}'
                         AND pos.snapshot_date = '{snapshot_date}'
                         AND pos.created_at_date = (SELECT Max(created_at_date)
                                                    FROM
                             {target_database_name}.monthly_pos
                             WHERE  product_code = '{product_code}'
                    AND snapshot_date = '{snapshot_date}')
                         AND pos.date <= '{snapshot_date}') AS pos
              ON dpd.partner_loan_id = pos.partner_loan_id
                 AND dpd.as_on_date = pos.date
       LEFT JOIN (SELECT npa.partner_loan_id,
                         npa.as_on_date,
                         npa.npa_tag
                  FROM   {target_database_name}.loan_npa AS npa
                  WHERE  npa.product_code = '{product_code}'
                         AND npa.snapshot_date = '{snapshot_date}'
                         AND npa.created_at_date = (SELECT Max(created_at_date)
                                                    FROM
                             {target_database_name}.loan_npa
                             WHERE  product_code = '{product_code}'
                    AND snapshot_date = '{snapshot_date}')
                         AND npa.as_on_date = '{snapshot_date}') AS npa
              ON dpd.partner_loan_id = npa.partner_loan_id
                 AND dpd.as_on_date = npa.as_on_date
       LEFT JOIN
       (
       SELECT 
          partner_loan_id,
          month_end_date,
          due_date,
          principal_due,
          interest_due,
          instalment_due
       FROM
       (
       SELECT 
          partner_loan_id,
          month_end_date,
          due_date,
          principal_due,
          interest_due,
          principal_due + interest_due AS instalment_due,
          rank() over (partition by partner_loan_id order by due_date desc) as rnk
       FROM {target_database_name}.financeschedule AS fs
                  WHERE  fs.product_code = '{product_code}'
                         AND fs.snapshot_date = '{snapshot_date}'
                         AND fs.created_at_date = (SELECT Max(created_at_date) FROM 
                         {target_database_name}.financeschedule
                         WHERE  product_code = '{product_code}'
                    AND snapshot_date = '{snapshot_date}')
                     AND due_date <= '{snapshot_date}'
       ) AS schedule
       WHERE schedule.rnk=1
       ) AS fs
       ON fs.partner_loan_id = dpd.partner_loan_id
       AND fs.month_end_date = dpd.as_on_date
       LEFT JOIN (SELECT fm.partner_loan_id,
                         fm.loan_amount,
                         fm.loan_start_date,
                         fm.maturity_date,
                         fm.vcal_loan_status,
                         fm.loan_status,
                         fm.loan_state,
                         fm.tenure,
                         fm.interest_rate,
                         fm.interest_type,
                         fm.loan_closed_date,
                         fm.interest_rate_frequency,
                         fm.vcal_bpi,
                         fm.loan_outstanding_amount,
                         fm.parent_restructured_loan_indicator,
                         fm.child_restructured_loan_indicator,
                         fm.loan_moratorium_indicator,
                         fm.snapshot_date,
                         fm.product_code,
                         json_extract_scalar(fm.extras, '$.credit_limit') AS credit_limit
                  FROM   {target_database_name}.financemain AS fm
                  WHERE  fm.product_code = '{product_code}'
                         AND fm.snapshot_date = '{snapshot_date}'
                         AND fm.created_at_date = (SELECT Max(created_at_date)
                                                   FROM
                         {target_database_name}.financemain
                         WHERE  product_code = '{product_code}'
                    AND snapshot_date = '{snapshot_date}')) AS fm
              ON fm.partner_loan_id = dpd.partner_loan_id
       LEFT JOIN (SELECT ls.partner_loan_id,
                         ls.loan_interest_accrued,
                         ls.loan_interest_accrued_not_due,
                         ls.loan_interest_overdue,
                         ls.loan_overdue,
                         ls.loan_interest_outstanding AS loan_interest_outstanding,
                         ls.ksf_loan_interest_outstanding,
                         ls.ksf_loan_interest_accrued,
                         ls.ksf_loan_interest_overdue,
                         ls.ksf_bpi_due,
                         ls.hurdle_rate
                  FROM   {target_database_name}.loan_book_summary AS ls
                  WHERE  ls.product_code = '{product_code}'
                         AND ls.snapshot_date = '{snapshot_date}'
                         AND ls.created_at_date = (SELECT Max(created_at_date)
                                                   FROM
                             {target_database_name}.loan_book_summary
                             WHERE  product_code = '{product_code}'
                    AND snapshot_date = '{snapshot_date}'))
                 AS ls
              ON ls.partner_loan_id = dpd.partner_loan_id
      LEFT JOIN (SELECT
         DISTINCT
         md.partner_loan_id,
                          md.partner_code,
                          md.los_loan_booking_id,
                          md.los_app_id,
                          md.credit_id
                   FROM   {target_database_name}.loan_metadata AS md
                   WHERE  md.product_code = '{product_code}'
                          AND md.snapshot_date = '{snapshot_date}'
                          AND md.created_at_date = (SELECT Max(created_at_date)
                                                    FROM
                              {target_database_name}.loan_metadata
                              WHERE  product_code = '{product_code}'
                     AND snapshot_date = '{snapshot_date}')) AS lm
               ON lm.partner_loan_id = dpd.partner_loan_id
       LEFT JOIN (SELECT disbursement.partner_loan_id,
                         disbursement.loan_disbursal_date,
                         disbursement.amount_disbursed,
                         disbursement.processing_fees
                  FROM   {target_database_name}.disbursement AS
                         disbursement
                  WHERE  disbursement.product_code = '{product_code}'
                         AND disbursement.snapshot_date = '{snapshot_date}'
                         AND disbursement.created_at_date = (SELECT
                             Max(created_at_date)
                                                             FROM
{target_database_name}.disbursement
WHERE  product_code = '{product_code}'
                    AND snapshot_date = '{snapshot_date}')) AS
                                   disbursement
ON disbursement.partner_loan_id = dpd.partner_loan_id
        LEFT JOIN (
                SELECT 
                wo.partner_loan_id,
                wo.write_off_date,
                       wo.state,
       wo.stage
                FROM   {target_database_name}.write_off_loans AS wo
    WHERE  wo.product_code = '{product_code}'
       AND wo.snapshot_date = '{snapshot_date}'
       AND wo.created_at_date = (SELECT Max(created_at_date)
                                 FROM
       {target_database_name}.write_off_loans
       WHERE  product_code = '{product_code}'
                    AND snapshot_date = '{snapshot_date}') 
    ) AS wo
    ON dpd.partner_loan_id = wo.partner_loan_id
    LEFT JOIN (
                SELECT 
                fldg.partner_loan_id,
                fldg.current_fldg_state,
                fldg.fldg_final_settlement_date,
                fldg.fldg_principal_settled
                FROM   {target_database_name}.fldg_summary AS fldg
    WHERE  fldg.product_code = '{product_code}'
       AND fldg.snapshot_date = '{snapshot_date}'
       AND fldg.created_at_date = (SELECT Max(created_at_date)
                                 FROM
       {target_database_name}.fldg_summary
       WHERE  product_code = '{product_code}'
                    AND snapshot_date = '{snapshot_date}' ) 
    ) AS fldg
    ON dpd.partner_loan_id = fldg.partner_loan_id
    LEFT JOIN (
        SELECT 
            partner_loan_id,
            sum(interest_paid) as total_interest_paid
        FROM
            {target_database_name}.repayment
        WHERE
            product_code = '{product_code}'
            AND snapshot_date = '{snapshot_date}'
            AND created_at_date = (SELECT max(created_at_date) 
                                    FROM {target_database_name}.repayment
                                    WHERE
                                        product_code = '{product_code}'
                                        AND snapshot_date = '{snapshot_date}'
                                )
        group by partner_loan_id
        ) as rp
    ON dpd.partner_loan_id = rp.partner_loan_id
    LEFT JOIN (
        SELECT 
            partner_loan_id,
            sum(interest_due) as total_interest_due
        FROM
            {target_database_name}.financeschedule
        WHERE
            product_code = '{product_code}'
            AND due_date <= '{snapshot_date}'
            AND snapshot_date = '{snapshot_date}'
            AND created_at_date = (SELECT max(created_at_date) 
                                    FROM {target_database_name}.financeschedule
                                    WHERE
                                        product_code = '{product_code}'
                                        AND snapshot_date = '{snapshot_date}'
                                )
            group by partner_loan_id
        ) as fs1
        on fs1.partner_loan_id = dpd.partner_loan_id
    FULL OUTER JOIN (
        SELECT distinct
            los_app_id,
            partner_app_id,
            customer_id,
            customer_state,
            customer_name,
            line_approved,
            pin_code,
            sanction_date,
            expiry_date
        FROM
            {target_database_name}.customer_metadata
        WHERE product_code = '{product_code}'
        and snapshot_date = '0000-00-00'
    ) as cm
    ON lm.los_app_id = cm.los_app_id
    LEFT JOIN (
        SELECT distinct
            state_code,
            state_name,
            pincode
        FROM
            {target_database_name}.pincode_state_mapping
    ) as sm
    ON cm.pin_code = sm.pincode
    --we are getting the finance_loan_status from the same source as monthly_loan_revenue_report
    LEFT JOIN(
        SELECT partner_loan_id,
         cast(json_extract_scalar(mr.revenue_summary, '$.finance_loan_status') AS varchar) AS finance_loan_status
        FROM {target_database_name}.monthly_revenue as mr
        WHERE
        snapshot_date = '{snapshot_date}' 
                    and product_code = '{product_code}'
                    and create_timestamp = (select max(create_timestamp)
                                          FROM {target_database_name}.monthly_revenue
                                          where snapshot_date = '{snapshot_date}' 
                                          and product_code = '{product_code}')
       ) as mr
    on mr.partner_loan_id=dpd.partner_loan_id
    LEFT JOIN(
    select
        loan_book_summary.partner_loan_id,
        loan_book_summary.loan_interest_due
    from {target_database_name}.loan_book_summary as loan_book_summary
    where 
        loan_book_summary.snapshot_date = '{snapshot_date}' 
        and loan_book_summary.product_code = '{product_code}'
        and loan_book_summary.create_timestamp = (select
                                    max(create_timestamp) 
                                from {target_database_name}.loan_book_summary
                                where 
                                    snapshot_date = '{snapshot_date}' 
                                     and product_code = '{product_code}')
        ) as loan_book_summary 
    on loan_book_summary.partner_loan_id = dpd.partner_loan_id 
) AS ecl
WHERE (ecl.loan_status <> 'cancelled'  OR ecl.loan_status is null) ) AS CLQ),

id_cal as (
    select
        partner_loan_id,
        calculated_cumulative_interest_due,
        calculated_cumulative_principal_due,
        'calculated' as calculated
        from vaultron_target.interest_due_calculated
    where product_code = '{product_code}'
      and snapshot_date = '{snapshot_date}'
      and created_at_date = (
        select max(created_at_date) from vaultron_target.interest_due_calculated
        where product_code = '{product_code}'
      and snapshot_date = '{snapshot_date}'
      )),

cal_ecl as (
    select 
    base_data.partner_loan_id,
    customer_name,
    loan_start_date,
    loan_closed_date,
    maturity_date,
    tenure,
    interest_rate,
    hurdle_rate,
    product_code,
    interest_type,
    credit_limit,
    loan_amount,
    finance_pos,
    finance_overdue_principal,
    finance_interest_outstanding,
    finance_interest_accrued_and_due,
    finance_interest_accrued_but_not_due,
    finance_total_overdue,
    excess_advance,
    restructured_flag,
    restructured_date,
    finance_dpd,
    finance_dpd_bucket,
    moratorium_loan_indicator,
    state_name,
    loan_ticket,
    partner_code,
    fldg_settled,
    finance_loan_status,
    fldg_final_settlement_date,
    ucic,
    credit_id,
    npa_tag,
    finance_pos_interest_rate,
    finance_pos_hurdle_rate,
    finance_pos_tenure,
    loan_type,
    partner_type,
    processing_fees,
    total_interest_due,
    as_on_date,
    ksf_loan_id,
    loan_status,
    loan_disbursal_date,
    interest_rate_frequency,
    Net_disbursed_amount,
    bpi_due,
    due_date,
    principal_due,
    interest_due,
    instalment_due,
    overdue_principal,
    interest_accrued_not_due,
    interest_accrued_and_due,
    interest_outstanding,
    ksf_interest_outstanding,
    ksf_interest_accrued_and_due,
    ksf_bpi_due,
    cumulative_principal_due,
    cumulative_principal_paid,
    overdue_interest,
    cumulative_interest_due,
    cumulative_interest_paid,
    loan_overdue,
    dpd_days,
    principal_outstanding,
    parent_restructured_loan_indicator,
    snapshot_date,
    write_off_date,
    state,
    stage,
    partner_loan_status,
    current_fldg_state,
    los_app_id,
    created_date,
    finance_ksf_interest_outstanding,
    finance_ksf_interest_accrued_and_due,
    finance_cumulative_overdue_principal,
    finance_cumulative_overdue_interest,
    calculated_cumulative_interest_due,
    calculated_cumulative_principal_due,
    calculated

    from base_data left join id_cal on base_data.partner_loan_id = id_cal.partner_loan_id
)

select 
   partner_loan_id,
    customer_name,
    loan_start_date,
    loan_closed_date,
    maturity_date,
    tenure,
    interest_rate,
    hurdle_rate,
    product_code,
    interest_type,
    credit_limit,
    loan_amount,
    finance_pos,
    finance_overdue_principal,
    finance_interest_outstanding,
    finance_interest_accrued_and_due,
    finance_interest_accrued_but_not_due,
    finance_total_overdue,
    excess_advance,
    restructured_flag,
    restructured_date,
    finance_dpd,
    finance_dpd_bucket,
    moratorium_loan_indicator,
    state_name,
    loan_ticket,
    partner_code,
    fldg_settled,
    finance_loan_status,
    fldg_final_settlement_date,
    ucic,
    credit_id,
    npa_tag,
    finance_pos_interest_rate,
    finance_pos_hurdle_rate,
    finance_pos_tenure,
    loan_type,
    partner_type,
    processing_fees,
    total_interest_due,
    as_on_date,
    ksf_loan_id,
    loan_status,
    loan_disbursal_date,
    interest_rate_frequency,
    Net_disbursed_amount,
    bpi_due,
    due_date,
    principal_due,
    interest_due,
    instalment_due,
    overdue_principal,
    interest_accrued_not_due,
    interest_accrued_and_due,
    interest_outstanding,
    ksf_interest_outstanding,
    ksf_interest_accrued_and_due,
    ksf_bpi_due,
    cumulative_principal_due,
    cumulative_principal_paid,
    CASE WHEN overdue_interest < 0 THEN 0
        ELSE overdue_interest END AS overdue_interest,
    cumulative_interest_due,
    cumulative_interest_paid,
    CASE WHEN calculated = 'calculated' AND overdue_interest < 0 THEN overdue_principal
         WHEN calculated = 'calculated' AND overdue_interest >= 0 THEN (overdue_principal + overdue_interest)
        ELSE loan_overdue END AS loan_overdue,
    dpd_days,
    principal_outstanding,
    parent_restructured_loan_indicator,
    snapshot_date,
    write_off_date,
    state,
    stage,
    partner_loan_status,
    current_fldg_state,
    los_app_id,
    created_date,
    finance_ksf_interest_outstanding,
    finance_ksf_interest_accrued_and_due,
    finance_cumulative_overdue_principal,
    finance_cumulative_overdue_interest

from (
    select
        partner_loan_id,
        customer_name,
        loan_start_date,
        loan_closed_date,
        maturity_date,
        tenure,
        interest_rate,
        hurdle_rate,
        product_code,
        interest_type,
        credit_limit,
        loan_amount,
        finance_pos,
        finance_overdue_principal,
        finance_interest_outstanding,
        finance_interest_accrued_and_due,
        finance_interest_accrued_but_not_due,
        finance_total_overdue,
        excess_advance,
        restructured_flag,
        restructured_date,
        finance_dpd,
        finance_dpd_bucket,
        moratorium_loan_indicator,
        state_name,
        loan_ticket,
        partner_code,
        fldg_settled,
        finance_loan_status,
        fldg_final_settlement_date,
        ucic,
        credit_id,
        npa_tag,
        finance_pos_interest_rate,
        finance_pos_hurdle_rate,
        finance_pos_tenure,
        loan_type,
        partner_type,
        processing_fees,
        total_interest_due,
        as_on_date,
        ksf_loan_id,
        loan_status,
        loan_disbursal_date,
        interest_rate_frequency,
        Net_disbursed_amount,
        bpi_due,
        due_date,
        principal_due,
        interest_due,
        instalment_due,
        overdue_principal,
        interest_accrued_not_due,
        interest_accrued_and_due,
        interest_outstanding,
        ksf_interest_outstanding,
        ksf_interest_accrued_and_due,
        ksf_bpi_due,
        CASE WHEN calculated = 'calculated' THEN calculated_cumulative_principal_due
           ELSE cumulative_principal_due END AS cumulative_principal_due,
        cumulative_principal_paid,
        CASE WHEN calculated = 'calculated' THEN (calculated_cumulative_interest_due - cumulative_interest_paid)
            ELSE overdue_interest END AS overdue_interest,

        CASE WHEN calculated = 'calculated' THEN calculated_cumulative_interest_due
           ELSE cumulative_interest_due END AS cumulative_interest_due,
        cumulative_interest_paid,
        loan_overdue,
        dpd_days,
        principal_outstanding,
        parent_restructured_loan_indicator,
        snapshot_date,
        write_off_date,
        state,
        stage,
        partner_loan_status,
        current_fldg_state,
        los_app_id,
        created_date,
        finance_ksf_interest_outstanding,
        finance_ksf_interest_accrued_and_due,
        finance_cumulative_overdue_principal,
        finance_cumulative_overdue_interest,
        calculated
from 
    (select * from cal_ecl))


'''