import * as React from 'react';
import axios from 'axios';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Divider from '@mui/material/Divider';
import Dialog from '@mui/material/Dialog';
import DialogContent from '@mui/material/DialogContent';
import DialogTitle from '@mui/material/DialogTitle';
import Grid from '@mui/material/Grid';
import NiceModal, { useModal } from '@ebay/nice-modal-react';
import TextField from '@mui/material/TextField';
import defaultSeedRuleData from '../mock-api/generateSeedRule';
import defaultRulesData from '../mock-api/listRules';
import databaseOptions from '../constants/databaseOptions';
import { FormLabel } from '@mui/material';
import MenuItem from '@mui/material/MenuItem';

const AddRewritingRule = NiceModal.create(() => {
  const modal = useModal();
  // Set up states for a rewriting rule
  const [name, setName] = React.useState("");
  const [database, setDatabase] = React.useState("postgresql");
  const [pattern, setPattern] = React.useState("");
  const [constraints, setConstraints] = React.useState("");
  const [rewrite, setRewrite] = React.useState("");
  const [actions, setActions] = React.useState("");
  // Set up states for an example rewriting pair
  const [q0, setQ0] = React.useState("");
  const [q1, setQ1] = React.useState("");

  const onNameChange = (event) => {
    setName(event.target.value);
  };

  const onDatabaseChange = (event) => {
    setDatabase(event.target.value);
  };

  const onPatternChange = (event) => {
    setPattern(event.target.value);
  };

  const onConstraintsChange = (event) => {
    setConstraints(event.target.value);
  };

  const onRewriteChange = (event) => {
    setRewrite(event.target.value);
  };

  const onActionsChange = (event) => {
    setActions(event.target.value);
  };

  const onQ0Change = (event) => {
    setQ0(event.target.value);
    onExampleChange();
  };

  const onQ1Change = (event) => {
    setQ1(event.target.value);
    onExampleChange();
  };

  const onExampleChange = () => {
    if (q0 != "" && q1 != "") {
      // post generateSeedRule request to server
      axios.post('/generateSeedRule', {'q0': q0, 'q1': q1})
      .then(function (response) {
        console.log('[/generateSeedRule] -> response:');
        console.log(response);
        // update the states for pattern and rewrite
        setPattern(response.data['pattern']);
        setRewrite(response.data['rewrite']);
      })
      .catch(function (error) {
        console.log('[/generateSeedRule] -> error:');
        console.log(error);
        // mock the result
        console.log(defaultSeedRuleData);
        setPattern(defaultSeedRuleData['pattern']);
        setRewrite(defaultSeedRuleData['rewrite']);
      });
    }
  };

  const onAdd = () => {
    if (pattern != "" && rewrite != "") {
      // post addRule request to server
      axios.post('/addRule', 
        {
          'name': name, 
          'pattern': pattern, 
          'constraints': constraints, 
          'rewrite': rewrite, 
          'actions': actions, 
          'database': database
        }
      )
      .then(function (response) {
        console.log('[/addRule] -> response:');
        console.log(response);
        modal.resolve(response);
        modal.hide();
      })
      .catch(function (error) {
        console.log('[/addRule] -> error:');
        console.log(error);
        // mock add rule to defaultRulesData
        defaultRulesData.push(
          {
            "id": 22,
            "key": "replace_strpos_upper",
            "name": "Replace Strpos Upper",
            "pattern": "STRPOS(UPPER(<x>),'<y>')>0",
            "constraints": "IS(y)=CONSTANT and\nTYPE(y)=STRING",
            "rewrite": "<x> ILIKE '%<y>%'",
            "actions": "",
            "enabled": false
          }
        );
        modal.resolve(error);
        modal.hide();
      });
    }
  };

  React.useEffect(() => {}, []);
  
  return (
    <Dialog
      open={modal.visible}
      onClose={() => modal.hide()}
      TransitionProps={{
        onExited: () => modal.remove(),
      }}
      fullWidth
      maxWidth={'lg'}
    >
      <DialogTitle>Add Rewriting Rule</DialogTitle>
      <DialogContent>
        <Grid sx={{ flexGrow: 1 }} container spacing={2}>
          <Grid item xs={12} sm={12} md={12} lg={12} xl={12}>
            <Grid container justifyContent="center" spacing={2}>
              <Grid item xs={12} sm={12} md={12} lg={12} xl={12}>
                <Box width="100%"/>
              </Grid>
              <Grid item xs={12} sm={12} md={12} lg={12} xl={12}>
                <Grid container justifyContent="center" spacing={2}>
                  <Grid item xs={8} sm={8} md={8} lg={8} xl={8}>
                    <TextField required id="name" label="Name" fullWidth value={name} onChange={onNameChange} />
                  </Grid>
                  <Grid item xs={4} sm={4} md={4} lg={4} xl={4}>
                    <TextField required select id="database" label="Database" fullWidth value={database} onChange={onDatabaseChange} >
                      {databaseOptions.map((option) => (
                        <MenuItem key={option.value} value={option.value}>
                          {option.label}
                        </MenuItem>
                      ))}
                    </TextField>
                  </Grid>
                </Grid>
              </Grid>
              <Grid item xs={12} sm={12} md={12} lg={12} xl={12}>
                <Box width="100%"/>
              </Grid>
              <Grid item xs={12} sm={12} md={12} lg={12} xl={12}>
                <Grid container justifyContent="center" spacing={2}>
                  <Grid item xs={4} sm={4} md={4} lg={4} xl={4}>
                    <TextField required id="pattern" label="Pattern" multiline fullWidth value={pattern} onChange={onPatternChange} />
                  </Grid>
                  <Grid item xs={2} sm={2} md={2} lg={2} xl={2}>
                    <TextField id="constraints" label="Constraints" multiline fullWidth value={constraints} onChange={onConstraintsChange} />
                  </Grid>
                  <Grid item xs={4} sm={4} md={4} lg={4} xl={4}>
                    <TextField required id="rewrite" label="Rewrite" multiline fullWidth value={rewrite} onChange={onRewriteChange} />
                  </Grid>
                  <Grid item xs={2} sm={2} md={2} lg={2} xl={2}>
                    <TextField id="actions" label="Actions" multiline fullWidth value={actions} onChange={onActionsChange} />
                  </Grid>
                  <Grid item xs={12} sm={12} md={12} lg={12} xl={12}>
                    <Button type="submit" variant="contained" color="primary" onClick={onAdd}>Add</Button>
                  </Grid>
                </Grid>
              </Grid>
              <Grid item xs={12} sm={12} md={12} lg={12} xl={12}>
                <Box width="100%"/>
              </Grid>
              <Divider />
              <Grid item xs={12} sm={12} md={12} lg={12} xl={12}>
                <Box width="100%"/>
              </Grid>
              <Grid item xs={12} sm={12} md={12} lg={12} xl={12}>
                <FormLabel>Formulating a Rule using Rewriting Example</FormLabel>
              </Grid>
              <Grid item xs={6} sm={6} md={6} lg={6} xl={6}>
                <TextField id="q0" label="Original SQL" multiline fullWidth onChange={onQ0Change} value={q0} />
              </Grid>
              <Grid item xs={6} sm={6} md={6} lg={6} xl={6}>
                <TextField id="q1" label="Rewritten SQL" multiline fullWidth onChange={onQ1Change} value={q1} />
              </Grid>
            </Grid>
          </Grid>
        </Grid>
      </DialogContent>
    </Dialog>
  );
});

export default AddRewritingRule;
