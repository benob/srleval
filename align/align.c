/* Copyright (C) (2009) (Benoit Favre) <favre@icsi.berkeley.edu>

This program is free software; you can redistribute it and/or 
modify it under the terms of the GNU General Public License 
as published by the Free Software Foundation; either 
version 3 of the License, or (at your option) any later 
version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA. */

#define _GNU_SOURCE
#define HAVE_PCRE
#include <stdio.h>
#include <stdlib.h>
#include <ctype.h>

#include "utils/common.h"
#include "utils/file.h"
#include "utils/vector.h"
#include "utils/string.h"
#include "utils/hashtable.h"

/* This program is freeware
   v3: added -i for case insensitive matches
   v2:
   v1: original release
*/

int32_t verbosity=0;

void align(int* align1,int* align2,int* id1, int length1,int* id2, int length2, double sub_penalty, double* ins_penalty, double* del_penalty, int compact)
{
	int i,j;
	char **backtrace=MALLOC(sizeof(char)*(length1+1)*(length2+1)+sizeof(char*)*(length1+1));
	double **matrix=MALLOC(sizeof(double)*(length1+1)*(length2+1)+sizeof(double*)*(length1+1));
	for(i=0;i<length1+1;i++)
	{
		backtrace[i]=(char*)((char*)backtrace+sizeof(char*)*(length1+1)+i*sizeof(char)*(length2+1));
		matrix[i]=(double*)((char*)matrix+sizeof(double*)*(length1+1)+i*sizeof(double)*(length2+1));
	}
	matrix[0][0]=0;
	backtrace[0][0]=0;
	for(i=1;i<length1+1;i++)
	{
		matrix[i][0]=i;
		backtrace[i][0]=1;
	}
	for(j=1;j<length2+1;j++)
	{
		matrix[0][j]=j;
		backtrace[0][j]=2;
	}
	for(i=1;i<length1+1;i++)
	{
		for(j=1;j<length2+1;j++)
		{
			double sub_value=matrix[i-1][j-1]+(id1[i-1]==id2[j-1]?0:sub_penalty);
			double del_value=matrix[i-1][j]+del_penalty[j - 1];
			double ins_value=matrix[i][j-1]+ins_penalty[i - 1];
            if(compact && j > 1 && j < length2) del_value += 1;
            if(compact && i > 1 && i < length1) ins_value += 1;
			if(sub_value<=del_value)
			{
				if(sub_value<=ins_value)
				{
					matrix[i][j]=sub_value;
					backtrace[i][j]=0;
				}
				else
				{
					matrix[i][j]=ins_value;
					backtrace[i][j]=2;
				}
			}
			else
			{
				if(del_value<ins_value)
				{
					matrix[i][j]=del_value;
					backtrace[i][j]=1;
				}
				else
				{
					matrix[i][j]=ins_value;
					backtrace[i][j]=2;
				}
			}
		}
	}
    if(verbosity > 2) {
        for(i=0;i<length1+1;i++)
        {
            for(j=0;j<length2+1;j++)
                fprintf(stderr,"%d ",backtrace[i][j]);
            fprintf(stderr,"| ");
            for(j=0;j<length2+1;j++)
                fprintf(stderr,"%.2f ",matrix[i][j]);
            fprintf(stderr,"\n");
        }
    }
    i=length1;
    j=length2;
    int where=length1+length2-1;
    while(i>0 || j>0)
    {
        if(backtrace[i][j]==0)
        {
            align1[where]=i-1;
            align2[where]=j-1;
            i--;j--;
        }
        else if(backtrace[i][j]==1)
        {
            align1[where]=i-1;
            align2[where]=-1;
            i--;
        }
        else
        {
            align1[where]=-1;
            align2[where]=j-1;
            j--;
        }
        where--;
    }
    while(where>0)
    {
        align1[where]=-1;
        align2[where]=-1;
        where--;
    }
    FREE(backtrace);
    FREE(matrix);
}

void usage(char* argv0)
{
	fprintf(stderr,"USAGE: %s [options] file1 file2\n",argv0);
	fprintf(stderr,"Performs a dynamic programming alignment of two sequences (one field per line in input files).\n");
	fprintf(stderr,"Benoit Favre <favre@icsi.berkeley.edu> 2008-02-11.\n");
	fprintf(stderr,"Warning: this program is O(n2) in file length (memory and time).\n");
	fprintf(stderr,"Options:\n");
	fprintf(stderr," --delimiter|-d <regex>         regular expression to split a line in fields (defaults to spaces: /[ \\t]+/)\n");
	fprintf(stderr," --field|-f <num>               field to use in alignment (defaults to 1)\n");
	fprintf(stderr," --grep|-g <regex>              only work on lines matching a given regular expression\n");
	fprintf(stderr," --skip|-s <regex>              skip lines matching a given regular expression (applied after grep)\n");
	fprintf(stderr," --verbose|-v <num>             verbosity level\n");
	fprintf(stderr," --sub-penalty|-sp <value>      substitution penalty (defaults to 1.0)\n");
	fprintf(stderr," --ins-penalty|-ip <value>      insertion penalty (defaults to 1.0)\n");
	fprintf(stderr," --del-penalty|-dp <value>      deletion penalty (defaults to 1.0)\n");
	fprintf(stderr," --cost-field|-cf <num>         a field in the input files is dedicated to the cost of an insertion/deletion (-1 = none)\n");
	fprintf(stderr," --ignore-case|-i               ignore case when comparing words\n");
	fprintf(stderr," --compact|-c                   allow free gaps before and after the shorter of the two inputs\n");
	fprintf(stderr," --line-numbers|-n              prepend input with line numbers (this modifies field numbers)\n");
	fprintf(stderr,"Use a suffix of 1 or 2 for file specific options (ex: -f1 3 -d2 \"_\" -s1 \"^#\").\n");
	fprintf(stderr,"If input files are in .gz format, they will be read using zlib.\n");
	fprintf(stderr,"Output (for each line from file1 and file2):\n");
	fprintf(stderr,"< line from file1 (or nothing if insertion)\n");
	fprintf(stderr,"> line from file2 (or nothing if deletion)\n");
	exit(1);
}

int main(int argc, char** argv)
{
	array_t* args=string_argv_to_array(argc,argv);
	string_t* arg=NULL;
	string_t* delimiter1=string_new("[ \t]+");
	string_t* delimiter2=string_new("[ \t]+");
	string_t* grep_pattern1=NULL;
	string_t* grep_pattern2=NULL;
	string_t* skip_pattern1=NULL;
	string_t* skip_pattern2=NULL;
	string_t* file1_name=NULL;
	string_t* file2_name=NULL;
    int ignore_case = 0;
	int field_number1=1;
	int field_number2=1;
    int cost_field1 = -1;
    int cost_field2 = -1;
    int compact = 0;
    int line_numbers = 0;
	double sub_penalty=1;
	double* ins_penalty = NULL;
	double* del_penalty = NULL;
    double ins_penalty_value = 1;
    double del_penalty_value = 1;
	while((arg=array_shift(args))!=NULL)
	{
		if(string_eq_cstr(arg,"-f") || string_eq_cstr(arg,"--field"))
		{
			string_free(arg);
			arg=array_shift(args);
			if(arg==NULL)usage(argv[0]);
			field_number1=string_to_int32(arg);
			field_number2=string_to_int32(arg);
		}
		else if(string_eq_cstr(arg,"-f1") || string_eq_cstr(arg,"--field1"))
		{
			string_free(arg);
			arg=array_shift(args);
			if(arg==NULL)usage(argv[0]);
			field_number1=string_to_int32(arg);
		}
		else if(string_eq_cstr(arg,"-f2") || string_eq_cstr(arg,"--field2"))
		{
			string_free(arg);
			arg=array_shift(args);
			if(arg==NULL)usage(argv[0]);
			field_number2=string_to_int32(arg);
		}
		else if(string_eq_cstr(arg,"-g") || string_eq_cstr(arg,"--grep"))
		{
			string_free(arg);
			arg=array_shift(args);
			if(arg==NULL)usage(argv[0]);
			grep_pattern1=string_copy(arg);
			grep_pattern2=string_copy(arg);
		}
		else if(string_eq_cstr(arg,"-g1") || string_eq_cstr(arg,"--grep1"))
		{
			string_free(arg);
			arg=array_shift(args);
			if(arg==NULL)usage(argv[0]);
			grep_pattern1=string_copy(arg);
		}
		else if(string_eq_cstr(arg,"-g2") || string_eq_cstr(arg,"--grep2"))
		{
			string_free(arg);
			arg=array_shift(args);
			if(arg==NULL)usage(argv[0]);
			grep_pattern2=string_copy(arg);
		}
		else if(string_eq_cstr(arg,"-s") || string_eq_cstr(arg,"--skip"))
		{
			string_free(arg);
			arg=array_shift(args);
			if(arg==NULL)usage(argv[0]);
			skip_pattern1=string_copy(arg);
			skip_pattern2=string_copy(arg);
		}
		else if(string_eq_cstr(arg,"-s1") || string_eq_cstr(arg,"--skip1"))
		{
			string_free(arg);
			arg=array_shift(args);
			if(arg==NULL)usage(argv[0]);
			skip_pattern1=string_copy(arg);
		}
		else if(string_eq_cstr(arg,"-s2") || string_eq_cstr(arg,"--skip2"))
		{
			string_free(arg);
			arg=array_shift(args);
			if(arg==NULL)usage(argv[0]);
			skip_pattern2=string_copy(arg);
		}
		else if(string_eq_cstr(arg,"-v") || string_eq_cstr(arg,"--verbose"))
		{
			string_free(arg);
			arg=array_shift(args);
			if(arg==NULL)usage(argv[0]);
			verbosity=string_to_int32(arg);
		}
		else if(string_eq_cstr(arg,"-d") || string_eq_cstr(arg,"--delimiter"))
		{
			string_free(arg);
			arg=array_shift(args);
			if(arg==NULL)usage(argv[0]);
			string_free(delimiter1);
			string_free(delimiter2);
			delimiter1=string_copy(arg);
			delimiter2=string_copy(arg);
		}
		else if(string_eq_cstr(arg,"-d1") || string_eq_cstr(arg,"--delimiter1"))
		{
			string_free(arg);
			arg=array_shift(args);
			if(arg==NULL)usage(argv[0]);
			string_free(delimiter1);
			delimiter1=string_copy(arg);
		}
		else if(string_eq_cstr(arg,"-d2") || string_eq_cstr(arg,"--delimiter2"))
		{
			string_free(arg);
			arg=array_shift(args);
			if(arg==NULL)usage(argv[0]);
			string_free(delimiter2);
			delimiter2=string_copy(arg);
		}
		else if(string_eq_cstr(arg,"-sp") || string_eq_cstr(arg,"--sub-penalty"))
		{
			string_free(arg);
			arg=array_shift(args);
			if(arg==NULL)usage(argv[0]);
			sub_penalty=string_to_double(arg);
		}
		else if(string_eq_cstr(arg,"-ip") || string_eq_cstr(arg,"--ins-penalty"))
		{
			string_free(arg);
			arg=array_shift(args);
			if(arg==NULL)usage(argv[0]);
			ins_penalty_value=string_to_double(arg);
		}
		else if(string_eq_cstr(arg,"-dp") || string_eq_cstr(arg,"--del-penalty"))
		{
			string_free(arg);
			arg=array_shift(args);
			if(arg==NULL)usage(argv[0]);
			del_penalty_value=string_to_double(arg);
		}
        else if(string_eq_cstr(arg, "-cf") || string_eq_cstr(arg, "--cost-field")) {
            string_free(arg);
            arg = array_shift(args);
            if(arg == NULL) usage(argv[0]);
            cost_field1 = string_to_int32(arg);
            cost_field2 = string_to_int32(arg);
        }
        else if(string_eq_cstr(arg, "-cf1") || string_eq_cstr(arg, "--cost-field1")) {
            string_free(arg);
            arg = array_shift(args);
            if(arg == NULL) usage(argv[0]);
            cost_field1 = string_to_int32(arg);
        }
        else if(string_eq_cstr(arg, "-cf2") || string_eq_cstr(arg, "--cost-field2")) {
            string_free(arg);
            arg = array_shift(args);
            if(arg == NULL) usage(argv[0]);
            cost_field2 = string_to_int32(arg);
        }
        else if(string_eq_cstr(arg, "-i") || string_eq_cstr(arg, "--ignore-case")) {
            ignore_case = 1;
        }
        else if(string_eq_cstr(arg, "-c") || string_eq_cstr(arg, "--compact")) {
            compact = 1;
        }
        else if(string_eq_cstr(arg, "-n") || string_eq_cstr(arg, "--line-numbers")) {
            line_numbers = 1;
        }
		else if(file1_name==NULL)
		{
			file1_name=string_copy(arg);
		}
		else if(file2_name==NULL)
		{
			file2_name=string_copy(arg);
		}
		else
		{
			usage(argv[0]);
		}
		string_free(arg);
	}
	array_free(args);
	if(file1_name==NULL || file2_name==NULL)usage(argv[0]);
	
	array_t* file1_lines=NULL;
	if(string_match(file1_name,"\\.gz$",NULL)) file1_lines=file_gz_readlines(file1_name->data);
	else file1_lines=file_readlines(file1_name->data);
	if(file1_lines==NULL)die("\"%s\"",file1_name->data);
    if(line_numbers != 0) {
        int i;
        for(i = 0;i < file1_lines->length; i++) {
            string_t* original = array_get(file1_lines, i);
		    string_chomp(original);
            string_t* with_line_number = string_sprintf("%d %s", i + 1, original->data);
            string_free(original);
            array_set(file1_lines, i, with_line_number);
        }
    }
	if(grep_pattern1!=NULL)
	{
		array_t* no_comment_file1_lines=string_array_grep(file1_lines,grep_pattern1->data,NULL);
		if(no_comment_file1_lines!=NULL)
		{
			string_array_free(file1_lines);
			file1_lines=no_comment_file1_lines;
		}
		else die("grep regex /%s/ matched no lines", grep_pattern1->data);
		string_free(grep_pattern1);
	}
	if(skip_pattern1!=NULL)
	{
		array_t* no_comment_file1_lines=string_array_grep(file1_lines,skip_pattern1->data,"!");
		if(no_comment_file1_lines!=NULL)
		{
			string_array_free(file1_lines);
			file1_lines=no_comment_file1_lines;
		}
		else die("skip regex /%s/ matched all lines", skip_pattern1->data);
		string_free(skip_pattern1);
	}

	array_t* file2_lines=NULL;
	if(string_match(file2_name,"\\.gz$",NULL)) file2_lines=file_gz_readlines(file2_name->data);
	else file2_lines=file_readlines(file2_name->data);
	if(file2_lines==NULL)die("\"%s\"",file2_name->data);
    if(line_numbers != 0) {
        int i;
        for(i = 0;i < file2_lines->length; i++) {
            string_t* original = array_get(file2_lines, i);
		    string_chomp(original);
            string_t* with_line_number = string_sprintf("%d %s", i + 1, original->data);
            string_free(original);
            array_set(file2_lines, i, with_line_number);
        }
    }
	if(grep_pattern2!=NULL)
	{
		array_t* no_comment_file2_lines=string_array_grep(file2_lines,grep_pattern2->data,NULL);
		if(no_comment_file2_lines!=NULL)
		{
			string_array_free(file2_lines);
			file2_lines=no_comment_file2_lines;
		}
		else die("grep regex /%s/ matched no lines", grep_pattern2->data);
		string_free(grep_pattern2);
	}
	if(skip_pattern2!=NULL)
	{
		array_t* no_comment_file2_lines=string_array_grep(file2_lines,skip_pattern2->data,"!");
		if(no_comment_file2_lines!=NULL)
		{
			string_array_free(file2_lines);
			file2_lines=no_comment_file2_lines;
		}
		else die("skip regex /%s/ matched all lines", skip_pattern2->data);
		string_free(skip_pattern2);
	}

	int* id1=MALLOC(sizeof(int)*file1_lines->length);
	int* id2=MALLOC(sizeof(int)*file2_lines->length);

	hashtable_t* token_to_id=hashtable_new();
	vector_t* tokens=vector_new(16);
	vector_push(tokens,strdup("UNK"));
	char* next_id=(char*)1;
	int i;
    ins_penalty = MALLOC((file1_lines->length + 1)*sizeof(double));
    del_penalty = MALLOC((file2_lines->length + 1)*sizeof(double));
    ins_penalty[file1_lines->length] = del_penalty_value;
    del_penalty[file2_lines->length] = ins_penalty_value;
	for(i=0;i<file1_lines->length;i++)
	{
        ins_penalty[i] = ins_penalty_value;
		string_t* line=array_get(file1_lines,i);
		string_chomp(line);
		array_t* fields=string_split(line,delimiter1->data,NULL);
		if(fields->length<field_number1)die("not enough fields, line %d in %s", i+1, file1_name->data);
		string_t* field=array_get(fields,field_number1-1);
        if(ignore_case) {
            int j;
            for(j = 0; j < field->length; j++) {
                field->data[j] = (char) tolower(field->data[j]);
            }
        }
		char* found=hashtable_get(token_to_id,field->data,field->length);
		if(found==NULL)
		{
			found=next_id;
			hashtable_set(token_to_id,field->data,field->length,found);
			vector_push(tokens, strdup(field->data));
			next_id++;
		}
		id1[i]=(int)found;
        if(cost_field1 > 0) {
            field = array_get(fields, cost_field1 - 1);
            ins_penalty[i] = string_to_double(field);
            //fprintf(stderr, "loading %f in %d\n", ins_penalty[i], i);
        }
		string_array_free(fields);
	}
	for(i=0;i<file2_lines->length;i++)
	{
        del_penalty[i] = del_penalty_value;
		string_t* line=array_get(file2_lines,i);
		string_chomp(line);
		array_t* fields=string_split(line,delimiter2->data,NULL);
		if(fields->length<field_number2)die("not enough fields, line %d in %s", i+1, file2_name->data);
		string_t* field=array_get(fields,field_number2-1);
        if(ignore_case) {
            int j;
            for(j = 0; j < field->length; j++) {
                field->data[j] = (char) tolower(field->data[j]);
            }
        }
		char* found=hashtable_get(token_to_id,field->data,field->length);
		if(found==NULL)
		{
			found=next_id;
			hashtable_set(token_to_id,field->data,field->length,found);
			vector_push(tokens, strdup(field->data));
			next_id++;
		}
		id2[i]=(int)found;
        if(cost_field2 > 0) {
            field = array_get(fields, cost_field2 - 1);
            del_penalty[i] = string_to_double(field);
            //fprintf(stderr, "loading %f in %d\n", del_penalty[i], i);
        }
		string_array_free(fields);
	}
	int* aligned1=MALLOC((file1_lines->length+file2_lines->length)*sizeof(int));
	memset(aligned1,-1,sizeof(int)*(file1_lines->length+file2_lines->length));
	int* aligned2=MALLOC((file1_lines->length+file2_lines->length)*sizeof(int));
	memset(aligned2,-1,sizeof(int)*(file1_lines->length+file2_lines->length));
	align(aligned1,aligned2,id1,file1_lines->length,id2,file2_lines->length, sub_penalty, ins_penalty, del_penalty, compact);
	
	int num_errors=0;
    int begin_offset_left = -1;
    int begin_offset_right = -1;
    int end_offset_left = 0;
    int end_offset_right = 0;
	for(i=0;i<file1_lines->length+file2_lines->length;i++)
	{
		if(aligned1[i]==-1 && aligned2[i]==-1)continue;
		if(aligned1[i]==-1)
		{
			string_t* line2=array_get(file2_lines,aligned2[i]);
			//fprintf(stdout,"map_i 0.0 0.0 # # %s\n",line2->data);
			fprintf(stdout,"< \n> %s\n",line2->data);
			if(verbosity>1)
				fprintf(stderr,"INS # %20s # %20s #\n","",(char*)vector_get(tokens,id2[aligned2[i]]));
            if(begin_offset_right == -1) begin_offset_right = num_errors;
            end_offset_right += 1;
            end_offset_left = 0;
			num_errors++;
		}
		else if(aligned2[i]==-1)
		{
			string_t* line1=array_get(file1_lines,aligned1[i]);
			//fprintf(stdout,"map_d 0.0 0.0 # %s # \n",line1->data);
			fprintf(stdout,"< %s\n> \n",line1->data);
			if(verbosity>1)
				fprintf(stderr,"DEL # %20s # %20s #\n",(char*)vector_get(tokens,id1[aligned1[i]]),"");
            if(begin_offset_left == -1) begin_offset_left = num_errors;
            end_offset_left += 1;
            end_offset_right = 0;
			num_errors++;
		}
		else
		{
			string_t* line1=array_get(file1_lines,aligned1[i]);
			string_t* line2=array_get(file2_lines,aligned2[i]);
			//fprintf(stdout,"map_m 0.0 0.0 # %s # %s \n",line1->data,line2->data);
			fprintf(stdout,"< %s\n> %s\n",line1->data,line2->data);
			char* match="   ";
			if(id2[aligned2[i]]!=id1[aligned1[i]])
			{
				match="SUB";
				num_errors++;
			}
            if(begin_offset_left == -1) begin_offset_left = num_errors;
            if(begin_offset_right == -1) begin_offset_right = num_errors;
            end_offset_right = 0;
            end_offset_left = 0;
			if(verbosity>1)
				fprintf(stderr,"%s # %20s # %20s #\n",match,(char*)vector_get(tokens,id1[aligned1[i]]),(char*)vector_get(tokens,id2[aligned2[i]]));
		}
	}
	if(verbosity>0)
	{
        int left_errors = num_errors;
        if(compact) left_errors -= begin_offset_left - end_offset_left;
        int right_errors = num_errors;
        if(compact) right_errors -= begin_offset_right - end_offset_right;
		fprintf(stderr,"WER left_ref: %.1f %% -- right_ref: %.1f %%\n",
            left_errors*100.0/file1_lines->length,right_errors*100.0/file2_lines->length);
	}
	string_free(delimiter1);
	string_free(delimiter2);
	string_free(file1_name);
	string_free(file2_name);
	string_array_free(file1_lines);
	string_array_free(file2_lines);
	hashtable_free(token_to_id);
	vector_apply(tokens, vector_freedata, NULL);
	vector_free(tokens);
	FREE(aligned1);
	FREE(aligned2);
    FREE(ins_penalty);
    FREE(del_penalty);
	FREE(id1);
	FREE(id2);
	return 0;
}
