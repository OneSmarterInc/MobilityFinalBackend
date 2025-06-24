from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from rest_framework import permissions
from authenticate.views import saveuserlog
from OnBoard.Organization.models import Organizations
from OnBoard.Company.models import Company
from Dashboard.ModelsByPage.DashAdmin import Vendors
from OnBoard.Ban.models import BaseDataTable


from django.db.models.functions import Cast
from django.db.models import FloatField

import matplotlib.pyplot as plt
from openpyxl import load_workbook
from openpyxl.drawing.image import Image
from openpyxl.styles import PatternFill
from io import BytesIO
from openpyxl.utils import get_column_letter
from openpyxl.styles import Font, Alignment, PatternFill
from openpyxl.styles import Font, Alignment, PatternFill
from openpyxl.styles import Font, Alignment, PatternFill
from openpyxl.styles import Font, Alignment, PatternFill
from openpyxl.styles import Font, Alignment, PatternFill
from django.db.models import Q
from django.core.files.base import ContentFile
from ..models import Report_Billed_Data
import pandas as pd
from ..ser import showBanSerializer, showBilledReport, OrganizationShowSerializer, VendorShowSerializer

from openpyxl import Workbook
from datetime import datetime
from ..models import Downloaded_reports
from collections import defaultdict
class ViewBilledReportView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def __init__(self, **kwargs):
        self.report_type = "Billed_Data_Usage"
        self.current_year = datetime.now().year
        self.data = None
        self.unique_dates = None
        super().__init__(**kwargs)

    def get(self, request,sub_type=None, *args, **kwargs):
        if request.user.designation.name == 'Admin':
            orgs = OrganizationShowSerializer(Organizations.objects.filter(company=request.user.company), many=True)
            vendors = VendorShowSerializer(Vendors.objects.all(), many=True)
            bans = showBanSerializer(BaseDataTable.objects.filter(company=request.user.company, viewuploaded=None, viewpapered=None), many=True)
        else:
            orgs = OrganizationShowSerializer(Organizations.objects.all(), many=True)
            vendors = VendorShowSerializer(Vendors.objects.all(), many=True)
            bans = showBanSerializer(BaseDataTable.objects.filter(viewuploaded=None, viewpapered=None), many=True)

        if not sub_type:
            self.data = showBilledReport(Report_Billed_Data.objects.all(), many=True)
        else:
            company = request.GET.get('company')
            sub_company = request.GET.get('sub_company')
            report_type = request.GET.get('report_type')
            month = request.GET.get('month')
            vendor = request.GET.get('vendor')
            year = request.GET.get('year')
            if not (company and sub_company and report_type and month and vendor and year):
                return Response({"message":"all data required!"},status=status.HTTP_400_BAD_REQUEST)
            filter_kwargs = {}
            if company:
                filter_kwargs['company'] = Company.objects.filter(Company_name=company)[0]
            if sub_company:
                filter_kwargs['organization'] = Organizations.objects.filter(Organization_name=sub_company)[0]
            if report_type:
                filter_kwargs['Report_Type'] = report_type
            if month:
                filter_kwargs['Month'] = month
            if year:
                filter_kwargs['Year'] = year
            if vendor:
                filter_kwargs['vendor'] = Vendors.objects.filter(name=vendor)[0]
            filtered_data = Report_Billed_Data.objects.filter(company=filter_kwargs['company'])
            if not filtered_data.exists():
                return Response({"message":f"no billed report found for {filter_kwargs['company'].Company_name}"},status=status.HTTP_400_BAD_REQUEST)
            
            filtered_data = filtered_data.filter(organization=filter_kwargs['organization'])
            if not filtered_data.exists():
                return Response({"message":f"no billed report found for {filter_kwargs['organization'].Organization_name}"},status=status.HTTP_400_BAD_REQUEST)
            
            filtered_data = filtered_data.filter(Report_Type=filter_kwargs['Report_Type'])
            if not filtered_data.exists():
                return Response({"message":f"no billed report found for {filter_kwargs['Report_Type']}"},status=status.HTTP_400_BAD_REQUEST)
            
            filtered_data = filtered_data.filter(Month=filter_kwargs['Month'])
            if not filtered_data.exists():
                return Response({"message":f"no billed report found for {filter_kwargs['Month']}"},status=status.HTTP_400_BAD_REQUEST)
            
            filtered_data = filtered_data.filter(Year=filter_kwargs['Year'])
            if not filtered_data.exists():
                return Response({"message":f"no billed report found for {filter_kwargs['Year']}"},status=status.HTTP_400_BAD_REQUEST)
            
            filtered_data = filtered_data.filter(vendor=filter_kwargs['vendor'])
            if not filtered_data.exists():
                return Response({"message":f"no billed report found for {filter_kwargs['vendor'].name}"},status=status.HTTP_400_BAD_REQUEST)
        
            if sub_type == "Top10BilledUsers":
                try:
                    filtered_data = filtered_data.annotate(
                        usage_float=Cast('Data_Usage_GB', FloatField())
                    ).order_by('-usage_float')[:10]
                    self.data = showBilledReport(filtered_data, many=True)
                except Exception as e:
                    print(e)
                    return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)   
            elif sub_type == "getZeroUsageReportbilledData":
                try:
                    filtered_data = Report_Billed_Data.objects.filter(
                        Q(Data_Usage_GB="0") | Q(Data_Usage_GB="0.0"),
                        **filter_kwargs
                    )
                    if not filtered_data.exists():
                        return Response({"message": "No data found for the given filters."}, status=status.HTTP_404_NOT_FOUND)
                    self.data = showBilledReport(filtered_data, many=True)
                except Exception as e:
                    print(e)
                    return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)  

            else:
                return Response({"message": "Invalid sub_type provided."}, status=status.HTTP_400_BAD_REQUEST)
        return Response(
            {"orgs": orgs.data, "vendors": vendors.data, "bans":bans.data, "data":self.data.data if self.data else None, "unique_dates":self.unique_dates if self.report_type == "Unbilled_Data_Usage" else None},
            status=status.HTTP_200_OK,
        )
        
    def change_kwargs(self,kwargs):
        if 'organization' in kwargs and str(kwargs['organization']) != str:
            kwargs['organization'] = kwargs['organization'].Organization_name
        if 'company' in kwargs and str(kwargs['company']) != str:
            kwargs['company'] = kwargs['company'].Company_name
        if 'vendor' in kwargs and str(kwargs['vendor']) != str:
            kwargs['vendor'] = kwargs['vendor'].name

        return kwargs

    def post(self, request,sub_type=None, *args, **kwargs):

        filter_kwargs = {}
        action = request.data.get('action')
        type = request.data.get('type')
        company = request.data.get('company')
        sub_company = request.data.get('sub_company')
        ban = request.data.get('ban')
        month = request.data.get('month')
        report_type = request.data.get('report_type')
        year = request.data.get('year')
        vendor = request.data.get('vendor')
        if not (company and sub_company and ban and report_type and month and vendor and year):
            return Response({"message":"all data required!"},status=status.HTTP_400_BAD_REQUEST)
        
        if company:
            filter_kwargs['company'] = Company.objects.filter(Company_name=company)[0]
        if sub_company:
            filter_kwargs['organization'] = Organizations.objects.filter(Organization_name=sub_company)[0]
        if ban:
            filter_kwargs['Account_Number'] = ban
        if report_type:
            filter_kwargs['Report_Type'] = report_type
        if month:
            filter_kwargs['Month'] = month
        if year:
            filter_kwargs['Year'] = year
        if vendor:
            filter_kwargs['vendor'] = Vendors.objects.filter(name=vendor)[0]

        filtered_data = Report_Billed_Data.objects.filter(company=filter_kwargs['company'])
        if not filtered_data.exists():
            return Response({"message":f"no billed report found for {filter_kwargs['company'].Company_name}"},status=status.HTTP_400_BAD_REQUEST)
        
        filtered_data = filtered_data.filter(organization=filter_kwargs['organization'])
        if not filtered_data.exists():
            return Response({"message":f"no billed report found for {filter_kwargs['organization'].Organization_name}"},status=status.HTTP_400_BAD_REQUEST)
        
        filtered_data = filtered_data.filter(Account_Number=filter_kwargs['Account_Number'])
        if not filtered_data.exists():
            return Response({"message":f"no billed report found for {filter_kwargs['Account_Number']}"},status=status.HTTP_400_BAD_REQUEST)

        filtered_data = filtered_data.filter(Report_Type=filter_kwargs['Report_Type'])
        if not filtered_data.exists():
            return Response({"message":f"no billed report found for {filter_kwargs['Report_Type']}"},status=status.HTTP_400_BAD_REQUEST)
        
        filtered_data = filtered_data.filter(Month=filter_kwargs['Month'])
        if not filtered_data.exists():
            return Response({"message":f"no billed report found for {filter_kwargs['Month']}"},status=status.HTTP_400_BAD_REQUEST)
        
        filtered_data = filtered_data.filter(Year=filter_kwargs['Year'])
        if not filtered_data.exists():
            return Response({"message":f"no billed report found for {filter_kwargs['Year']}"},status=status.HTTP_400_BAD_REQUEST)
        
        filtered_data = filtered_data.filter(vendor=filter_kwargs['vendor'])
        if not filtered_data.exists():
            return Response({"message":f"no billed report found for {filter_kwargs['vendor'].name}"},status=status.HTTP_400_BAD_REQUEST)
        if not filtered_data.exists():
            return Response({"message": "No data found for the given filters."}, status=200)
        
        if not sub_type:
            try:
                filtered_data = Report_Billed_Data.objects.filter(company=filter_kwargs['company'])
                if not filtered_data.exists():
                    return Response({"message":f"no billed report found for {filter_kwargs['company'].Company_name}"},status=status.HTTP_400_BAD_REQUEST)
                
                filtered_data = filtered_data.filter(organization=filter_kwargs['organization'])
                if not filtered_data.exists():
                    return Response({"message":f"no billed report found for {filter_kwargs['organization'].Organization_name}"},status=status.HTTP_400_BAD_REQUEST)
                
                filtered_data = filtered_data.filter(Report_Type=filter_kwargs['Report_Type'])
                if not filtered_data.exists():
                    return Response({"message":f"no billed report found for {filter_kwargs['Report_Type']}"},status=status.HTTP_400_BAD_REQUEST)
                
                filtered_data = filtered_data.filter(Month=filter_kwargs['Month'])
                if not filtered_data.exists():
                    return Response({"message":f"no billed report found for {filter_kwargs['Month']}"},status=status.HTTP_400_BAD_REQUEST)
                
                filtered_data = filtered_data.filter(Year=filter_kwargs['Year'])
                if not filtered_data.exists():
                    return Response({"message":f"no billed report found for {filter_kwargs['Year']}"},status=status.HTTP_400_BAD_REQUEST)
                
                filtered_data = filtered_data.filter(vendor=filter_kwargs['vendor'])
                if not filtered_data.exists():
                    return Response({"message":f"no billed report found for {filter_kwargs['vendor'].name}"},status=status.HTTP_400_BAD_REQUEST)
                if not filtered_data.exists():
                    return Response({"message": "No data found for the given filters."}, status=200)

                # Create a list of dictionaries to store the data in the required format
                report_data = []
                for record in filtered_data:
                    report_data.append({
                        "accountNumber": record.Account_Number,
                        'wirelessNumber': record.Wireless_Number,
                        'userName': record.User_Name,
                        'vendor': record.vendor.name,
                        'voicePlanUsage': float(record.Voice_Plan_Usage),  # New column
                        'messagingUsage': float(record.Messaging_Usage),  # New column
                        'usage': float(record.Data_Usage_GB),
                    })

                # Convert the data to a pandas DataFrame
                df = pd.DataFrame(report_data)

                # Categorize data usage into specified ranges
                bins = [0, 0.001, 1, 5, 7.5, 12.5, 22, float('inf')]
                labels = ['Equal to 0', 'Less than 1 GB', '1-5 GB', '5-7.5 GB', '7.5-12.5 GB', '12.5-22 GB', '22 GB plus']
                df['usage_category'] = pd.cut(df['usage'], bins=bins, labels=labels, right=False)

                # Reorder columns and include new fields, removing 'date'
                df = df[['accountNumber', 'wirelessNumber', 'userName', 'vendor', 'voicePlanUsage', 'messagingUsage', 'usage', 'usage_category']]

                # Generate a bar graph for data usage categories
                if vendor:
                    df_vendor = df[df['vendor'] == vendor]
                else:
                    df_vendor = df

                usage_counts = df_vendor['usage_category'].value_counts().reindex(labels, fill_value=0)
                plt.figure(figsize=(12, 6))
                usage_counts.plot(kind='bar')
                plt.title(f'Data Usage Frequency for Vendor: {vendor}')
                plt.xlabel('Data Usage Category')
                plt.ylabel('Frequency')
                plt.xticks(rotation=45, ha='right')
                plt.tight_layout()  # Adjust the padding to fit the labels

                # Save the plot to a BytesIO object
                plot_output = BytesIO()
                plt.savefig(plot_output, format='png')
                plot_output.seek(0)

                # Create an Excel writer object and write the DataFrame to it
                output = BytesIO()
                writer = pd.ExcelWriter(output, engine='openpyxl')
                df.to_excel(writer, index=False, sheet_name='Billed Data Report')
                writer.close()
                output.seek(0)

                # Load the workbook and insert the image
                workbook = load_workbook(output)
                worksheet = workbook['Billed Data Report']
                img = Image(plot_output)
                worksheet.add_image(img, 'K2')  # Adjust the position as needed

                # Insert a dynamic heading
                heading = f'{month} Usage Report'
                worksheet.insert_rows(1)  # Shift everything down to make space for the header
                worksheet.merge_cells('A1:H1')  # Adjust the merge to fit the new columns
                heading_cell = worksheet['A1']
                heading_cell.value = heading
                heading_cell.font = Font(bold=True, color='FFFFFF', size=14)
                heading_cell.fill = PatternFill(start_color='000080', end_color='000080', fill_type='solid')
                heading_cell.alignment = Alignment(horizontal='center', vertical='center')

                # Define the background fill colors for 'usage' column based on conditions
                red_fill = PatternFill(start_color="FF0000", end_color="FF0000", fill_type="solid")
                light_yellow_fill = PatternFill(start_color="FFFFE0", end_color="FFFFE0", fill_type="solid")
                dark_navy_fill = PatternFill(start_color="000080", end_color="000080", fill_type="solid")

                # Define light blue fill for Voice_Plan_Usage, Messaging_Usage, and usage_category columns
                light_blue_fill = PatternFill(start_color="ADD8E6", end_color="ADD8E6", fill_type="solid")

                # Apply specific formatting for the 'usage' column header (set text color to black)
                usage_header_cell = worksheet["G2"]  # Assuming 'G2' is the header for the usage column
                usage_header_cell.font = Font(bold=True, color="000000")  # Set usage header text to black

                # Adjust column widths based on the content and header
                for col_num, column_cells in enumerate(worksheet.columns, 1):
                    max_length = 0
                    column = get_column_letter(col_num)

                    for cell in column_cells:
                        try:
                            if cell.value:
                                max_length = max(max_length, len(str(cell.value)))

                            # Apply background color and text formatting to specific columns
                            if column == 'G':  # Assuming 'G' is usage column
                                usage_value = cell.value
                                if isinstance(usage_value, float) or isinstance(usage_value, int):
                                    # Set content text color to white
                                    cell.font = Font(color="FFFFFF")
                                    # Apply conditional formatting based on usage values
                                    if usage_value == 0:
                                        cell.fill = red_fill
                                    elif 0 < usage_value <= 1:
                                        cell.fill = light_yellow_fill
                                    elif usage_value > 1:
                                        cell.fill = dark_navy_fill
                            elif column in ['E', 'F', 'H']:  # Voice_Plan_Usage, Messaging_Usage, usage_category columns
                                cell.fill = light_blue_fill
                        except:
                            pass

                    adjusted_width = (max_length + 2) if max_length < 30 else 30
                    worksheet.column_dimensions[column].width = adjusted_width

                # Save the modified workbook to the output
                output_with_image = BytesIO()
                workbook.save(output_with_image)
                output_with_image.seek(0)
                
                report_file = Downloaded_reports(
                    report_type=report_type,
                    kwargs=self.change_kwargs(filter_kwargs)
                )
                report_file.file.save(f'billed_data_report_{month}_{year}.xlsx', ContentFile(output_with_image.getvalue()))
                return Response({"data":report_file.file.url, "message" : "Excel file generated sucessfully!"}, status=status.HTTP_200_OK)

            except Exception as e:
                print(e)
                return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        else:
            if sub_type == "getZeroUsageReportbilledExcel":
                try:
                    filtered_data = Report_Billed_Data.objects.filter(
                        Q(Data_Usage_GB="0") | Q(Data_Usage_GB="0.0"),
                        **filter_kwargs
                    )
                    if not filtered_data.exists():
                        return Response({"message": "No data found for the given filters."}, status=status.HTTP_404_NOT_FOUND)

                    # Extract the unique vendor name from the filtered data
                    unique_vendor = filtered_data.values_list('vendor', flat=True).distinct()
                    if unique_vendor:
                        vendor_name = unique_vendor[0]  # Get the first unique vendor name
                    else:
                        vendor_name = "Unknown Vendor"  # Fallback in case there's no vendor

                    # Create a list of dictionaries to store the data in the required format
                    report_data = []
                    for record in filtered_data:
                        report_data.append({
                            "accountNumber": record.Account_Number,
                            'wirelessNumber': record.Wireless_Number,
                            'userName': record.User_Name,
                            'dataUsageGB': record.Data_Usage_GB,
                        })

                    # Convert the data to a pandas DataFrame
                    df = pd.DataFrame(report_data)

                    # Create an Excel writer object and write the DataFrame to it
                    output = BytesIO()
                    writer = pd.ExcelWriter(output, engine='openpyxl')
                    df.to_excel(writer, index=False, sheet_name='Zero Usage Billed Data Report')
                    writer.close()
                    output.seek(0)

                    # Load the workbook to apply formatting
                    workbook = load_workbook(output)
                    worksheet = workbook['Zero Usage Billed Data Report']

                    # Add the main heading for the report (dynamic based on month and vendor)
                    main_heading = f'{month} Zero Usage Report ({vendor_name})'
                    worksheet.insert_rows(1)
                    worksheet.merge_cells('A1:D1')  # Adjust the merge to cover the required columns
                    heading_cell = worksheet['A1']
                    heading_cell.value = main_heading
                    heading_cell.font = Font(bold=True, color="FFFFFF", size=14)
                    heading_cell.alignment = Alignment(horizontal="center", vertical="center")
                    heading_cell.fill = PatternFill(start_color='000080', end_color='000080', fill_type='solid')  # Dark navy blue background

                    # Define the background fill for 'dataUsageGB' column
                    light_yellow_fill = PatternFill(start_color="FFFFE0", end_color="FFFFE0", fill_type="solid")

                    # Get the index of the 'dataUsageGB' column (4th column in this case)
                    data_usage_column_index = df.columns.get_loc('dataUsageGB') + 1  # Pandas index is 0-based, Excel is 1-based
                    
                    # Apply background color to 'dataUsageGB' column (4th column)
                    for row in worksheet.iter_rows(min_row=3, min_col=data_usage_column_index, max_col=data_usage_column_index):
                        for cell in row:
                            cell.fill = light_yellow_fill

                    # Adjust column widths based on content and header
                    for col_num, column_cells in enumerate(worksheet.columns, 1):
                        max_length = 0
                        column = get_column_letter(col_num)
                        
                        for cell in column_cells:
                            try:
                                if cell.value:
                                    max_length = max(max_length, len(str(cell.value)))
                            except:
                                pass

                        adjusted_width = (max_length + 2) if max_length < 30 else 30  # Adjust maximum column width to 30 characters
                        worksheet.column_dimensions[column].width = adjusted_width
                    output_with_formatting = BytesIO()
                    workbook.save(output_with_formatting)
                    output_with_formatting.seek(0)

                    report_file = Downloaded_reports(
                        report_type=report_type,
                        kwargs=self.change_kwargs(filter_kwargs)
                    )
                    report_file.file.save(f'zero_usage_billed_data_report_{month}_{year}.xlsx', ContentFile(output_with_formatting.getvalue()))
                    return Response({"data": report_file.file.url, "message" : "Excel file generated sucessfully!"}, status=status.HTTP_200_OK)

                    # response = HttpResponse(output_with_formatting, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                    # response['Content-Disposition'] = f'attachment; filename=zero_usage_billed_data_report_{month}_{year}.xlsx'

                    # return response

                except Exception as e:
                    print(e)
                    return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            elif sub_type == "getTop10BilledUsers":
                try:
                    filtered_data = Report_Billed_Data.objects.filter(**filter_kwargs).annotate(
                        usage_float=Cast('Data_Usage_GB', FloatField())
                    ).order_by('-usage_float')[:10]

                    # Create a list of dictionaries to store the data in the required format
                    report_data = []
                    for record in filtered_data:
                        report_data.append({
                            "accountNumber": record.Account_Number,
                            'wirelessNumber': record.Wireless_Number,
                            'userName': record.User_Name,
                            'dataUsageGB': float(record.Data_Usage_GB),
                        })

                    # Convert the data to a pandas DataFrame
                    df = pd.DataFrame(report_data, columns=['accountNumber', 'wirelessNumber', 'userName', 'dataUsageGB'])

                    # Create a bar graph for the top 10 data usage
                    plt.figure(figsize=(10, 6))
                    df.plot(kind='bar', x='userName', y='dataUsageGB', legend=False)
                    plt.title(f'Top 10 Data Usage for Vendor: {vendor}')
                    plt.xlabel('User Name')
                    plt.ylabel('Data Usage (GB)')
                    plt.xticks(rotation=45, ha='right')
                    plt.tight_layout()

                    # Save the plot to a BytesIO object
                    plot_output = BytesIO()
                    plt.savefig(plot_output, format='png')
                    plot_output.seek(0)

                    # Create a new BytesIO output for the Excel file
                    output = BytesIO()

                    # Write the DataFrame to an Excel file using pandas
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        df.to_excel(writer, index=False, sheet_name='Top 10 Usage Billed Data Report')

                    # Reopen the Excel file for additional formatting with openpyxl
                    output.seek(0)
                    workbook = load_workbook(output)
                    worksheet = workbook['Top 10 Usage Billed Data Report']

                    # Insert the plot image into the worksheet
                    img = Image(plot_output)
                    worksheet.add_image(img, 'F2')

                    # Insert a dynamic heading for the top of the report
                    main_heading = f'{month} Top 10 Data Usage ({vendor})'
                    worksheet.insert_rows(1)
                    worksheet.merge_cells('A1:D1')
                    heading_cell = worksheet['A1']
                    heading_cell.value = main_heading
                    heading_cell.font = Font(bold=True, color="FFFFFF", size=14)
                    heading_cell.alignment = Alignment(horizontal="center", vertical="center")
                    heading_cell.fill = PatternFill(start_color='000080', end_color='000080', fill_type='solid')

                    # Apply formatting to the 'dataUsageGB' column and adjust column widths
                    dark_navy_fill = PatternFill(start_color="000080", end_color="000080", fill_type="solid")
                    white_font = Font(color="FFFFFF")
                    for row in worksheet.iter_rows(min_row=3, max_row=worksheet.max_row, min_col=4, max_col=4):
                        for cell in row:
                            cell.fill = dark_navy_fill
                            cell.font = white_font

                    for col_num, column_cells in enumerate(worksheet.columns, 1):
                        max_length = 0
                        column = get_column_letter(col_num)
                        for cell in column_cells:
                            if cell.value:
                                max_length = max(max_length, len(str(cell.value)))
                        adjusted_width = (max_length + 2) if max_length < 30 else 30
                        worksheet.column_dimensions[column].width = adjusted_width

                    # Save the workbook with formatting
                    output_with_formatting = BytesIO()
                    workbook.save(output_with_formatting)
                    output_with_formatting.seek(0)

                    report_file = Downloaded_reports(
                        report_type = report_type,
                        kwargs = self.change_kwargs(filter_kwargs)
                    )
                    report_file.file.save(f'top_10_usage_billed_data_report_{month}_{year}.xlsx', ContentFile(output_with_formatting.getvalue()))
                    return Response({"data": report_file.file.url, "message" : "Excel file generated successfully!"}, status=status.HTTP_200_OK)

                except Exception as e:
                    return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)